#!/usr/bin/env python3
"""Script to find the GL100 device and display its USB information.

This helper script scans for USB devices and can help identify the
GL100's vendor and product IDs.
"""

import usb.core
import usb.util


def list_usb_devices():
    """List all USB devices connected to the system."""
    devices = usb.core.find(find_all=True)

    print("Connected USB Devices:")
    print("=" * 80)

    for dev in devices:
        try:
            print(f"\nVendor ID:  0x{dev.idVendor:04x}")
            print(f"Product ID: 0x{dev.idProduct:04x}")

            try:
                manufacturer = usb.util.get_string(dev, dev.iManufacturer)
                product = usb.util.get_string(dev, dev.iProduct)
                print(f"Manufacturer: {manufacturer}")
                print(f"Product: {product}")
            except:
                pass

            print(f"Bus: {dev.bus}, Address: {dev.address}")

            # Show configuration
            for cfg in dev:
                print(f"  Configuration: {cfg.bConfigurationValue}")
                for intf in cfg:
                    print(f"    Interface: {intf.bInterfaceNumber}")
                    print(f"      Class: {intf.bInterfaceClass}")
                    for ep in intf:
                        print(f"      Endpoint: 0x{ep.bEndpointAddress:02x}")

        except Exception as e:
            print(f"Error reading device: {e}")

        print("-" * 80)


def find_mooer_devices():
    """Try to identify potential Mooer devices."""
    devices = usb.core.find(find_all=True)

    print("\nSearching for potential Mooer/GL100 devices...")
    print("=" * 80)

    # Known Mooer vendor IDs and GL100 product IDs
    KNOWN_MOOER_VENDOR_IDS = [0x34db]  # Mooer Corporation
    KNOWN_GL100_IDS = [(0x34db, 0x0008)]  # GL100

    found = False
    for dev in devices:
        try:
            manufacturer = ""
            product = ""
            is_gl100 = False

            try:
                if dev.iManufacturer:
                    manufacturer = usb.util.get_string(dev, dev.iManufacturer).lower()
                if dev.iProduct:
                    product = usb.util.get_string(dev, dev.iProduct).lower()
            except:
                pass

            # Check by USB ID first (most reliable)
            if (dev.idVendor, dev.idProduct) in KNOWN_GL100_IDS:
                is_gl100 = True
            # Check by vendor ID
            elif dev.idVendor in KNOWN_MOOER_VENDOR_IDS:
                is_gl100 = True
            # Check by string descriptors
            elif 'mooer' in manufacturer or 'mooer' in product or \
                 'gl100' in product or 'looper' in product:
                is_gl100 = True
            # Check for devices with the expected endpoint configuration (0x02, 0x81, 0x83)
            else:
                endpoints = set()
                try:
                    for cfg in dev:
                        for intf in cfg:
                            for ep in intf:
                                endpoints.add(ep.bEndpointAddress)
                    if 0x02 in endpoints and 0x81 in endpoints and 0x83 in endpoints:
                        is_gl100 = True
                except:
                    pass

            if is_gl100:
                found = True
                print(f"\n✓ GL100 device found!")
                print(f"Vendor ID:  0x{dev.idVendor:04x}")
                print(f"Product ID: 0x{dev.idProduct:04x}")
                if manufacturer:
                    print(f"Manufacturer: {manufacturer}")
                if product:
                    print(f"Product: {product}")

                # Check if IDs are already updated
                if dev.idVendor == 0x34db and dev.idProduct == 0x0008:
                    print("\n✓ Device IDs are already configured in src/gl100/usb_device.py")
                else:
                    print("\nUpdate the following in src/gl100/usb_device.py:")
                    print(f"  VENDOR_ID = 0x{dev.idVendor:04x}")
                    print(f"  PRODUCT_ID = 0x{dev.idProduct:04x}")
                print("-" * 80)

        except Exception as e:
            pass

    if not found:
        print("\nNo obvious Mooer/GL100 devices found.")
        print("Please plug in your GL100 and run this script again.")
        print("\nIf the device is connected, look through the list above")
        print("for a device with vendor-specific endpoints at 0x02, 0x81, 0x83")


if __name__ == "__main__":
    print("GL100 USB Device Finder")
    print("=" * 80)
    print()

    list_usb_devices()
    find_mooer_devices()

    print("\n" + "=" * 80)
    print("Done!")
