#!/usr/bin/env python3
"""Simple test to send one command and read response."""

import usb.core
import usb.util
import time

VENDOR_ID = 0x34DB
PRODUCT_ID = 0x0008

def main():
    print("=" * 60)
    print("GL100 Simple Communication Test")
    print("=" * 60)

    # Find and setup device
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is None:
        print("ERROR: Device not found")
        return

    print(f"✓ Found device: Bus {dev.bus}, Address {dev.address}")

    # Detach kernel drivers
    for intf in [0, 1]:
        try:
            if dev.is_kernel_driver_active(intf):
                dev.detach_kernel_driver(intf)
                print(f"✓ Detached kernel driver from interface {intf}")
        except:
            pass

    dev.set_configuration()
    usb.util.claim_interface(dev, 0)
    usb.util.claim_interface(dev, 1)
    print("✓ Configured and claimed interfaces")

    print("\n" + "=" * 60)
    print("Sending initialization command...")
    print("=" * 60)

    # First command from Windows: 3F AA 55 01 00 00 ...
    init_cmd = bytearray(64)
    init_cmd[0:3] = bytes([0x3F, 0xAA, 0x55])
    init_cmd[3] = 0x01
    init_cmd[4] = 0x00
    init_cmd[5] = 0x00

    print(f"Init command: {' '.join(f'{b:02x}' for b in init_cmd[:16])}")

    try:
        written = dev.write(0x02, init_cmd, timeout=2000)
        print(f"✓ Wrote {written} bytes to endpoint 0x02")

        # Read response
        try:
            data = dev.read(0x83, 1024, timeout=2000)
            print(f"✓ Init response ({len(data)} bytes): {' '.join(f'{b:02x}' for b in data[:32])}")
        except usb.core.USBTimeoutError:
            print("  (No response to init)")

        time.sleep(0.1)
    except Exception as e:
        print(f"✗ Init failed: {e}")

    print("\n" + "=" * 60)
    print("Sending query command for slot 0...")
    print("=" * 60)

    # Query command with CRC
    from gl100.protocol import GL100Protocol
    cmd = GL100Protocol.create_query_track_command(0)

    print(f"Query command: {' '.join(f'{b:02x}' for b in cmd[:16])}")

    try:
        # Write to endpoint 0x02
        written = dev.write(0x02, cmd, timeout=2000)
        print(f"✓ Wrote {written} bytes to endpoint 0x02")
    except Exception as e:
        print(f"✗ Write failed: {e}")
        return

    # Try reading from endpoint 0x83
    print("\nAttempting to read response from endpoint 0x83...")
    try:
        data = dev.read(0x83, 1024, timeout=2000)
        print(f"✓ Received {len(data)} bytes:")
        print(f"  {' '.join(f'{b:02x}' for b in data[:32])}")
        if len(data) > 32:
            print(f"  ... ({len(data)-32} more bytes)")
    except usb.core.USBTimeoutError:
        print("✗ Timeout - no response from device")
    except Exception as e:
        print(f"✗ Read failed: {e}")

    # Try reading from endpoint 0x81
    print("\nAttempting to read from endpoint 0x81...")
    try:
        data = dev.read(0x81, 1024, timeout=1000)
        print(f"✓ Received {len(data)} bytes from 0x81:")
        print(f"  {' '.join(f'{b:02x}' for b in data[:32])}")
    except usb.core.USBTimeoutError:
        print("  (Timeout - expected, no data on this endpoint)")
    except Exception as e:
        print(f"  Error: {e}")

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
