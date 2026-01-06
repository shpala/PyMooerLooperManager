#!/usr/bin/env python3
"""Compare responses from full vs empty slots to identify track presence pattern."""

import usb.core
import usb.util
import time
import sys

VENDOR_ID = 0x34DB
PRODUCT_ID = 0x0008

def main():
    print("=" * 60)
    print("GL100 Slot Response Comparison")
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
    print("✓ Configured and claimed interfaces\n")

    # Import protocol for CRC
    sys.path.insert(0, '/home/shpala/dev/gl100/src')
    from gl100.protocol import GL100Protocol

    # Query slots: 0-3 (should have tracks), 50, 99 (should be empty)
    test_slots = [0, 1, 2, 3, 50, 99]

    responses = {}

    for slot in test_slots:
        print("=" * 60)
        print(f"Querying slot {slot}...")
        print("=" * 60)

        cmd = GL100Protocol.create_query_track_command(slot)
        print(f"Command: {' '.join(f'{b:02x}' for b in cmd[:16])}")

        try:
            written = dev.write(0x02, cmd, timeout=2000)
            print(f"✓ Wrote {written} bytes")

            # Read response
            try:
                data = dev.read(0x83, 1024, timeout=2000)
                responses[slot] = bytes(data)
                print(f"✓ Received {len(data)} bytes")
                print(f"\nFirst 64 bytes:")
                for i in range(0, min(64, len(data)), 16):
                    hex_str = ' '.join(f'{b:02x}' for b in data[i:i+16])
                    ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
                    print(f"  {i:04x}: {hex_str:<48} {ascii_str}")
                print()
            except usb.core.USBTimeoutError:
                print("✗ Timeout - no response")
                responses[slot] = None
        except Exception as e:
            print(f"✗ Error: {e}")
            responses[slot] = None

        time.sleep(0.1)

    # Analysis
    print("\n" + "=" * 60)
    print("ANALYSIS")
    print("=" * 60)

    print("\nComparing first 32 bytes of each response:\n")
    print("Slot | Bytes 0-15                                        | Bytes 16-31")
    print("-----+---------------------------------------------------+---------------------------------------------------")

    for slot in test_slots:
        if responses[slot]:
            data = responses[slot]
            hex1 = ' '.join(f'{b:02x}' for b in data[:16])
            hex2 = ' '.join(f'{b:02x}' for b in data[16:32])
            print(f"  {slot:2d} | {hex1:<49} | {hex2}")
        else:
            print(f"  {slot:2d} | (no response)")

    print("\n" + "=" * 60)
    print("Looking for differences...")
    print("=" * 60)

    # Compare full slots (0-3) vs empty slots (50, 99)
    full_slots = [0, 1, 2, 3]
    empty_slots = [50, 99]

    # Check if we have valid responses
    full_responses = [responses[s] for s in full_slots if responses[s] is not None]
    empty_responses = [responses[s] for s in empty_slots if responses[s] is not None]

    if full_responses and empty_responses:
        print("\nByte-by-byte comparison (first 32 bytes):\n")
        print("Byte | Full slots (0-3)          | Empty slots (50,99)       | Different?")
        print("-----+---------------------------+---------------------------+-----------")

        for byte_idx in range(32):
            full_vals = set(r[byte_idx] for r in full_responses if len(r) > byte_idx)
            empty_vals = set(r[byte_idx] for r in empty_responses if len(r) > byte_idx)

            full_str = '{' + ','.join(f'{v:02x}' for v in sorted(full_vals)) + '}'
            empty_str = '{' + ','.join(f'{v:02x}' for v in sorted(empty_vals)) + '}'

            different = "YES" if full_vals != empty_vals and len(full_vals) > 0 and len(empty_vals) > 0 else ""

            print(f"  {byte_idx:2d} | {full_str:<25} | {empty_str:<25} | {different}")

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
