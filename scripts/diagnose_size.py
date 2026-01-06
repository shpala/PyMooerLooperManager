#!/usr/bin/env python3
"""Diagnostic script to analyze size reporting from GL100 device."""

import sys
import logging
import struct

# Add src to path
sys.path.insert(0, "src")

from gl100.usb_device import GL100Device

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """Analyze size reporting for slot 0."""
    device = GL100Device()

    print("=" * 70)
    print("GL100 Size Diagnostic Tool")
    print("=" * 70)

    if not device.connect():
        print("ERROR: Could not connect to GL100 device")
        print("Make sure:")
        print("  1. Device is powered on and connected via USB")
        print("  2. You have permission to access USB devices")
        print("  3. VENDOR_ID and PRODUCT_ID are correct in usb_device.py")
        return 1

    print("\nConnected to GL100")
    print("\nQuerying slot 0...")

    # Query slot 0 directly
    cmd = device.protocol.create_query_track_command(0)
    device._write(cmd)
    response = device._read(size=1024, endpoint=0x83, timeout=1000)

    print(f"\nRaw response ({len(response)} bytes):")
    print(f"  Hex: {response[:32].hex()}")
    print()

    if len(response) >= 8:
        # Parse according to current understanding
        has_track_byte = response[0]
        size_bytes_4_7 = struct.unpack("<I", response[4:8])[0]
        size_bytes_1_4 = struct.unpack("<I", response[1:5])[0]

        print("Parsed values:")
        print(f"  Byte 0 (has_track): 0x{has_track_byte:02x} = {has_track_byte}")
        print(f"  Bytes 1-4 (alt): {size_bytes_1_4:,} bytes = {size_bytes_1_4 / (1024**2):.2f} MB")
        print(
            f"  Bytes 4-7 (current): {size_bytes_4_7:,} bytes = {size_bytes_4_7 / (1024**2):.2f} MB"
        )
        print()

        # Calculate what these would mean for different interpretations
        print("If bytes 4-7 represent:")
        print(f"  24-bit size: {size_bytes_4_7:,} bytes")
        print(
            f"    → 16-bit equivalent: {size_bytes_4_7 * 2 // 3:,} bytes = {(size_bytes_4_7 * 2 // 3) / (1024**2):.2f} MB"
        )
        print(
            f"    → Duration: {size_bytes_4_7 / (44100 * 3 * 2):.2f} seconds = {size_bytes_4_7 / (44100 * 3 * 2) / 60:.2f} minutes"
        )
        print()
        print(f"  16-bit size: {size_bytes_4_7:,} bytes")
        print(
            f"    → 24-bit equivalent: {size_bytes_4_7 * 3 // 2:,} bytes = {(size_bytes_4_7 * 3 // 2) / (1024**2):.2f} MB"
        )
        print(
            f"    → Duration: {size_bytes_4_7 / (44100 * 2 * 2):.2f} seconds = {size_bytes_4_7 / (44100 * 2 * 2) / 60:.2f} minutes"
        )
        print()
        print(f"  Number of samples: {size_bytes_4_7:,} samples")
        print(
            f"    → 16-bit bytes: {size_bytes_4_7 * 2 * 2:,} bytes = {(size_bytes_4_7 * 2 * 2) / (1024**2):.2f} MB"
        )
        print(
            f"    → 24-bit bytes: {size_bytes_4_7 * 3 * 2:,} bytes = {(size_bytes_4_7 * 3 * 2) / (1024**2):.2f} MB"
        )
        print(
            f"    → Duration: {size_bytes_4_7 / 44100:.2f} seconds = {size_bytes_4_7 / 44100 / 60:.2f} minutes"
        )
        print()
        print(f"  Number of frames (stereo pairs): {size_bytes_4_7:,} frames")
        print(
            f"    → 16-bit bytes: {size_bytes_4_7 * 2 * 2:,} bytes = {(size_bytes_4_7 * 2 * 2) / (1024**2):.2f} MB"
        )
        print(
            f"    → 24-bit bytes: {size_bytes_4_7 * 3 * 2:,} bytes = {(size_bytes_4_7 * 3 * 2) / (1024**2):.2f} MB"
        )
        print(
            f"    → Duration: {size_bytes_4_7 / 44100:.2f} seconds = {size_bytes_4_7 / 44100 / 60:.2f} minutes"
        )

    print("\n" + "=" * 70)
    print("Now download the track and check:")
    print("  1. What file size does the WAV file have on disk?")
    print("  2. What is the duration when you play it?")
    print("  3. Compare with the values above to determine the correct interpretation")
    print("=" * 70)

    device.disconnect()
    return 0


if __name__ == "__main__":
    sys.exit(main())
