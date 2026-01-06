#!/usr/bin/env python3
"""Test script to experiment with GL100 USB communication."""

import usb.core
import usb.util
import time

# GL100 USB IDs
VENDOR_ID = 0x34DB
PRODUCT_ID = 0x0008

def main():
    print("GL100 Communication Test")
    print("=" * 60)

    # Find device
    dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
    if dev is None:
        print("ERROR: GL100 device not found")
        return

    print(f"✓ Found GL100: Bus {dev.bus}, Address {dev.address}")

    # Detach kernel drivers
    for interface in [0, 1]:
        try:
            if dev.is_kernel_driver_active(interface):
                dev.detach_kernel_driver(interface)
                print(f"✓ Detached kernel driver from interface {interface}")
        except Exception as e:
            print(f"  Note: Interface {interface}: {e}")

    # Set configuration
    dev.set_configuration()
    print("✓ Set configuration")

    # Claim interfaces
    usb.util.claim_interface(dev, 0)
    usb.util.claim_interface(dev, 1)
    print("✓ Claimed interfaces 0 and 1")

    print("\n" + "=" * 60)
    print("Testing different command patterns...")
    print("=" * 60)

    # Test 1: Try to read spontaneous data
    print("\n1. Checking for spontaneous data on endpoint 0x83...")
    try:
        data = dev.read(0x83, 64, timeout=1000)
        print(f"   Received {len(data)} bytes:")
        print(f"   {' '.join(f'{b:02x}' for b in data)}")
    except usb.core.USBTimeoutError:
        print("   No data (timeout)")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Try simple command on endpoint 0x02
    print("\n2. Sending test command on endpoint 0x02...")
    test_cmd = bytes([0xAA, 0x55] + [0x00] * 62)
    try:
        written = dev.write(0x02, test_cmd, timeout=1000)
        print(f"   Wrote {written} bytes")

        # Try to read response on 0x83
        try:
            data = dev.read(0x83, 1024, timeout=2000)
            print(f"   Response on 0x83: {len(data)} bytes")
            print(f"   {' '.join(f'{b:02x}' for b in data[:64])}")
        except usb.core.USBTimeoutError:
            print("   No response on 0x83")

        # Try to read response on 0x81
        try:
            data = dev.read(0x81, 64, timeout=1000)
            print(f"   Response on 0x81: {len(data)} bytes")
            print(f"   {' '.join(f'{b:02x}' for b in data)}")
        except usb.core.USBTimeoutError:
            print("   No response on 0x81")

    except Exception as e:
        print(f"   Error: {e}")

    # Test 3: Try commands on endpoint 0x03 (interface 1)
    print("\n3. Sending test command on endpoint 0x03...")
    try:
        written = dev.write(0x03, test_cmd, timeout=1000)
        print(f"   Wrote {written} bytes")

        # Try to read response
        try:
            data = dev.read(0x83, 1024, timeout=2000)
            print(f"   Response: {len(data)} bytes")
            print(f"   {' '.join(f'{b:02x}' for b in data[:64])}")
        except usb.core.USBTimeoutError:
            print("   No response")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 60)
    print("Done! Check the output above for clues about the protocol.")
    print("=" * 60)

    # Cleanup
    usb.util.release_interface(dev, 0)
    usb.util.release_interface(dev, 1)
    for interface in [0, 1]:
        try:
            dev.attach_kernel_driver(interface)
        except:
            pass

if __name__ == "__main__":
    main()
