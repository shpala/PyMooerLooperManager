#!/usr/bin/env python3
"""Test if device is responsive"""

from gl100.usb_device import GL100Device
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

device = GL100Device()
print("Attempting to connect...")
if not device.connect():
    print("Failed to connect")
    exit(1)

print("Connected!")

try:
    print("\nTesting device responsiveness by querying slot 4...")

    # Try the same command that list_tracks uses
    cmd = device.protocol.create_query_track_command(4)
    device._write(cmd)
    print("  Command sent successfully")

    # Try to read response
    print("  Reading response...")
    response = device._read(size=1024, endpoint=0x83, timeout=5000)
    print(f"  Received {len(response)} bytes")
    print(f"  First 20 bytes: {response[:20].hex()}")

    # Parse header
    exists, size = device.protocol.parse_track_info_header(response)
    print(f"  Track exists: {exists}")
    print(f"  Track size: {size} bytes")

    print("\n✓ Device is responsive!")

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    device.disconnect()
    print("\nDisconnected")
