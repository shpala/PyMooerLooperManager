#!/usr/bin/env python3
"""Debug download process to understand the protocol."""

import usb.core
import usb.util
import sys

VENDOR_ID = 0x34DB
PRODUCT_ID = 0x0008

sys.path.insert(0, '/home/shpala/dev/gl100/src')
from gl100.protocol import GL100Protocol, crc16

def main():
    print("=" * 60)
    print("GL100 Download Debug")
    print("=" * 60)

    # Find and setup device
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is None:
        print("ERROR: Device not found")
        return

    print(f"✓ Found device\n")

    # Detach kernel drivers
    for intf in [0, 1]:
        try:
            if dev.is_kernel_driver_active(intf):
                dev.detach_kernel_driver(intf)
        except:
            pass

    dev.set_configuration()
    usb.util.claim_interface(dev, 0)
    usb.util.claim_interface(dev, 1)

    slot = 0
    print(f"Attempting to download track from slot {slot}\n")

    # Send download command for chunk 0 (with CRC)
    cmd = bytearray(64)
    cmd[0:3] = bytes([0x3F, 0xAA, 0x55])
    cmd[3] = 0x07  # CMD_TRACK_OPS
    cmd[4] = 0x00
    cmd[5] = 0x82  # SUBCMD_DOWNLOAD
    cmd[6] = slot
    cmd[7] = 0x00  # chunk low
    cmd[8] = 0x00  # chunk high

    # Calculate CRC
    crc = crc16(cmd[3:12])
    cmd[12] = (crc >> 8) & 0xFF
    cmd[13] = crc & 0xFF

    print(f"Chunk 0 command: {' '.join(f'{b:02x}' for b in cmd[:16])}")

    try:
        written = dev.write(0x02, bytes(cmd), timeout=2000)
        print(f"✓ Wrote {written} bytes\n")

        # Try to read response
        print("Reading response on endpoint 0x83...")
        try:
            data = dev.read(0x83, 1024, timeout=5000)
            print(f"✓ Received {len(data)} bytes")
            print(f"\nFirst 64 bytes:")
            for i in range(0, min(64, len(data)), 16):
                hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
                print(f"  {i:04x}: {hex_str}")

            # Check if this looks like audio data or metadata
            print(f"\nByte 0: 0x{data[0]:02x} (0x01 = has track)")
            if len(data) >= 8:
                size = int.from_bytes(data[4:8], 'little')
                print(f"Bytes 4-7 (size): {size} bytes")

        except usb.core.USBTimeoutError:
            print("✗ Timeout - no response")
        except Exception as e:
            print(f"✗ Error reading: {e}")

    except Exception as e:
        print(f"✗ Write failed: {e}")

    print("\n" + "=" * 60)
    print("Cleaning up...")
    usb.util.release_interface(dev, 0)
    usb.util.release_interface(dev, 1)
    for intf in [0, 1]:
        try:
            dev.attach_kernel_driver(intf)
        except:
            pass
    print("Done!")

if __name__ == "__main__":
    main()
