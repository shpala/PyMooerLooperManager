#!/usr/bin/env python3
"""Analyze play commands from packet capture"""

import subprocess
import re

# Get all frames in the play/pause range with endpoint 0x02 (host to device)
result = subprocess.run([
    'tshark', '-r', 'gl100.pcapng',
    '-Y', 'frame.number >= 824611 && frame.number <= 826814 && usb.src == "host" && usb.endpoint_address == 0x02',
    '-x'
], capture_output=True, text=True, stderr=subprocess.DEVNULL)

# Parse commands
commands = []
for line in result.stdout.split('\n'):
    if '3f aa 55' in line:
        # Extract the hex bytes
        hex_part = line[50:].strip()  # Get the ASCII part
        # Get next line which has the command
        idx = result.stdout.split('\n').index(line)
        if idx + 1 < len(result.stdout.split('\n')):
            next_line = result.stdout.split('\n')[idx + 1]
            # Extract bytes from offset 0x20
            match = re.search(r'0020\s+([0-9a-f ]+)', next_line)
            if match:
                hex_bytes = match.group(1).replace(' ', '')
                # Command starts at 3f aa 55 which is at byte 11 (0x1d) in the URB
                # In the 0020 line, we need bytes starting from position 0
                if len(hex_bytes) >= 26:  # Need at least 13 bytes (26 hex chars)
                    cmd = hex_bytes[:26]  # Get first 13 bytes
                    commands.append(cmd)

print(f"Found {len(commands)} commands")
print("\nFirst 20 commands:")
for i, cmd in enumerate(commands[:20]):
    # Parse: 3faa55 07 00 8a BB 00 SSSS 0000 CCCC
    if len(cmd) >= 26:
        header = cmd[0:6]
        cmd_type = cmd[6:8]
        pad1 = cmd[8:10]
        subcmd = cmd[10:12]
        byte6 = cmd[12:14]
        byte7 = cmd[14:16]
        slot_bytes = cmd[16:20]
        slot = int(slot_bytes[2:4] + slot_bytes[0:2], 16) if len(slot_bytes) == 4 else 0

        print(f"{i+1:3d}. subcmd=0x{subcmd} byte6=0x{byte6} slot={slot}")
