#!/usr/bin/env python3
"""Download track 4 and compare with GL_LOOPFILE_04.wav"""

import scipy.io.wavfile as wav
import numpy as np
from gl100.usb_device import GL100Device
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def main():
    # Load reference file
    print("Loading reference file GL_LOOPFILE_04.wav...")
    _, win_data = wav.read("GL_LOOPFILE_04.wav")
    print(f"  Shape: {win_data.shape}, dtype: {win_data.dtype}")

    # Connect to device
    print("\nConnecting to GL100...")
    device = GL100Device()
    if not device.connect():
        print("ERROR: Failed to connect to device")
        return 1

    try:
        # Download track from slot 4
        print("Downloading track from slot 4...")
        audio_data = device.download_track(slot=4)
        print(f"  Downloaded shape: {audio_data.shape}, dtype: {audio_data.dtype}")

        # Save to file
        wav.write("track_4.wav", 44100, audio_data)
        print("  Saved to track_4.wav")

        # Compare
        print("\n" + "="*70)
        print("VERIFICATION")
        print("="*70)

        if audio_data.shape != win_data.shape:
            print(f"✗ Shape mismatch: {audio_data.shape} vs {win_data.shape}")
            return 1

        if np.array_equal(audio_data, win_data):
            print("✓ SUCCESS! Files match perfectly!")
            print("  All 44,100 frames are identical")
            return 0
        else:
            num_diff = np.sum(audio_data != win_data)
            total = audio_data.size
            print(f"✗ Files differ: {num_diff}/{total} values ({100*num_diff/total:.2f}%)")

            # Show first difference
            for i in range(min(len(audio_data), len(win_data))):
                if not np.array_equal(audio_data[i], win_data[i]):
                    print(f"\n  First difference at frame {i}:")
                    print(f"    Windows: {win_data[i].tolist()}")
                    print(f"    GL100:   {audio_data[i].tolist()}")
                    break

            # Find offset
            print("\n  Checking for frame offset...")
            for gl_idx in range(min(10, len(audio_data))):
                for win_idx in range(min(10, len(win_data))):
                    if np.array_equal(audio_data[gl_idx], win_data[win_idx]):
                        offset = win_idx - gl_idx
                        print(f"  GL100[{gl_idx}] = Windows[{win_idx}] (offset: {offset} frames)")
                        break

            return 1

    finally:
        device.disconnect()

if __name__ == "__main__":
    exit(main())
