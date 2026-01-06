#!/usr/bin/env python3
"""Debug the download process."""

import sys
sys.path.insert(0, 'src')

from gl100.usb_device import GL100Device
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

print("Connecting to GL100...")
device = GL100Device()
device.connect()

try:
    print("\nDownloading track from slot 4 with detailed logging...")
    audio = device.download_track(4)

    print(f"\n{'='*60}")
    print(f"Download completed!")
    print(f"  Final shape: {audio.shape}")
    print(f"  Expected: (44100, 2)")
    print(f"  Got frames: {audio.shape[0]:,}")
    print(f"  Missing: {44100 - audio.shape[0]:,}")

finally:
    device.disconnect()
