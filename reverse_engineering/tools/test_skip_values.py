#!/usr/bin/env python3
"""Test what skip value gives us the correct alignment."""

import scipy.io.wavfile as wav
import numpy as np

_, win_data = wav.read("GL_LOOPFILE_04.wav")
_, gl_data = wav.read("track_4.wav")

print("Current state (with 24-byte skip):")
print(f"GL100 frame 0: {gl_data[0].tolist()}")
print(f"Windows frame 4: {win_data[4].tolist()}")
print(f"Match: {np.array_equal(gl_data[0], win_data[4])}")

print("\n" + "="*70)
print("What we need:")
print("="*70)
print(f"GL100 frame 0 should be: {win_data[0].tolist()} (Windows frame 0)")
print(f"GL100 is currently reading from what would be Windows frame 4")
print(f"\nTo go from frame 4 to frame 0, we need to skip LESS by 4 frames")
print(f"4 frames × 6 bytes/frame = 24 bytes less")
print(f"Current skip: 24 bytes")
print(f"New skip: 24 - 24 = 0 bytes")
print(f"\n→ Audio data starts at byte 0 (no header in download chunks!)")
