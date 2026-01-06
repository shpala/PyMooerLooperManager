
import sys
import os
import scipy.io.wavfile as wav
import numpy as np
import logging
import usb.core
import time
from gl100.usb_device import GL100Device

logging.basicConfig(level=logging.INFO)

def main():
    # 1. Reset device
    print("Resetting device...")
    dev_find = usb.core.find(idVendor=0x34DB, idProduct=0x0008)
    if dev_find:
        try:
            dev_find.reset()
            print("Reset command sent.")
        except Exception as e:
            print(f"Reset failed: {e}")
    time.sleep(5)

    # 2. Connect
    dev = GL100Device()
    if not dev.connect():
        print("Could not connect to GL100")
        return

    try:
        slot = 5
        input_file = "track_4.wav"
        
        # 3. Load Audio
        rate, original_audio = wav.read(input_file)
        print(f"Loaded {input_file}: shape={original_audio.shape}")

        # 4. DELETE Slot 5 first
        print(f"\nDeleting slot {slot}...")
        try:
            dev.delete_track(slot)
            print("Delete command sent.")
        except Exception as e:
            print(f"Delete failed: {e}")
        time.sleep(1)

        # 5. Upload to Slot 5
        print(f"\nUploading to slot {slot}...")
        dev.upload_track(slot, original_audio)
        print("Upload complete!")

        # 6. Download from Slot 5
        print(f"\nDownloading from slot {slot}...")
        downloaded_audio = dev.download_track(slot)
        print("Download complete!")

        # 7. Compare
        print("\nVerifying...")
        min_len = min(len(original_audio), len(downloaded_audio))
        orig_slice = original_audio[:min_len]
        down_slice = downloaded_audio[:min_len]

        if np.array_equal(orig_slice, down_slice):
            print("✓ SUCCESS! Uploaded and downloaded audio match perfectly!")
        else:
            diff_count = np.sum(orig_slice != down_slice)
            total = orig_slice.size
            print(f"✗ FAILURE! Files differ in {diff_count}/{total} values ({100*diff_count/total:.2f}%)")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        dev.disconnect()

if __name__ == "__main__":
    main()
