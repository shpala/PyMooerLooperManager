#!/usr/bin/env python3
"""Download slot 4 using the GUI's GL100Worker approach"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal
import scipy.io.wavfile as wav
import numpy as np
from gl100.usb_device import GL100Device
import logging

logging.basicConfig(level=logging.DEBUG)

class DownloadWorker(QThread):
    """Worker thread for downloading track"""
    finished = pyqtSignal(object)  # Emits audio data or None on error
    error = pyqtSignal(str)

    def __init__(self, slot):
        super().__init__()
        self.slot = slot

    def run(self):
        device = GL100Device()
        try:
            if not device.connect():
                self.error.emit("Failed to connect to device")
                return

            # Download track
            audio_data = device.download_track(self.slot)
            self.finished.emit(audio_data)

        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(None)
        finally:
            device.disconnect()


def main():
    app = QApplication(sys.argv)

    print("Starting download of slot 4...")

    worker = DownloadWorker(slot=4)

    def on_finished(audio_data):
        if audio_data is not None:
            print(f"\nDownload successful!")
            print(f"  Shape: {audio_data.shape}")
            print(f"  Dtype: {audio_data.dtype}")

            # Save to file
            wav.write("track_4.wav", 44100, audio_data)
            print("  Saved to track_4.wav")

            # Compare with reference
            try:
                _, win_data = wav.read("GL_LOOPFILE_04.wav")
                if np.array_equal(audio_data, win_data):
                    print("\n✓ SUCCESS! File matches GL_LOOPFILE_04.wav perfectly!")
                else:
                    print("\n✗ File differs from GL_LOOPFILE_04.wav")
                    # Find first difference
                    for i in range(min(len(audio_data), len(win_data))):
                        if not np.array_equal(audio_data[i], win_data[i]):
                            print(f"  First difference at frame {i}:")
                            print(f"    Windows: {win_data[i].tolist()}")
                            print(f"    GL100:   {audio_data[i].tolist()}")
                            break
            except Exception as e:
                print(f"  Could not compare: {e}")
        else:
            print("\nDownload failed")

        app.quit()

    def on_error(msg):
        print(f"\nError: {msg}")
        app.quit()

    worker.finished.connect(on_finished)
    worker.error.connect(on_error)
    worker.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
