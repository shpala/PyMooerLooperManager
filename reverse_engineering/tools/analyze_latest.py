#!/usr/bin/env python3
"""Analyze the latest download."""

import scipy.io.wavfile as wav
import numpy as np

print("Loading files...")
rate1, win_data = wav.read("GL_LOOPFILE_04.wav")
rate2, gl_data = wav.read("track_4.wav")

print("\n" + "="*70)
print("FILE COMPARISON")
print("="*70)

print(f"\nWindows GUI (GL_LOOPFILE_04.wav):")
print(f"  Shape: {win_data.shape}")
print(f"  Frames: {win_data.shape[0]:,}")
print(f"  Duration: {win_data.shape[0] / rate1:.4f} seconds")
print(f"  Data bytes: {win_data.nbytes:,}")
print(f"  File size: 352,844 (44 header + {win_data.nbytes:,} data)")

print(f"\nGL100 Download (track_4.wav):")
print(f"  Shape: {gl_data.shape}")
print(f"  Frames: {gl_data.shape[0]:,}")
print(f"  Duration: {gl_data.shape[0] / rate2:.4f} seconds")
print(f"  Data bytes: {gl_data.nbytes:,}")
print(f"  File size: 348,188 (44 header + {gl_data.nbytes:,} data)")

print(f"\nDifference:")
frames_diff = win_data.shape[0] - gl_data.shape[0]
bytes_diff = win_data.nbytes - gl_data.nbytes
print(f"  Missing frames: {frames_diff:,}")
print(f"  Missing bytes: {bytes_diff:,}")
print(f"  Missing time: {frames_diff / rate1:.4f} seconds")
print(f"  Percentage: {100 * gl_data.shape[0] / win_data.shape[0]:.2f}%")

# Check first frames
print(f"\n" + "="*70)
print("CONTENT COMPARISON")
print("="*70)

print(f"\nFirst 5 frames:")
print(f"Windows GUI:")
for i in range(5):
    print(f"  [{i}] {win_data[i]}")

print(f"\nGL100 Download:")
for i in range(5):
    print(f"  [{i}] {gl_data[i]}")

# Check if the overlap matches
overlap = min(win_data.shape[0], gl_data.shape[0])
match = np.array_equal(win_data[:overlap], gl_data[:overlap])
print(f"\nFirst {overlap:,} frames match: {match}")

if not match:
    # Find first difference
    for i in range(min(100, overlap)):
        if not np.array_equal(win_data[i], gl_data[i]):
            print(f"\nFirst difference at frame {i}:")
            print(f"  Windows: {win_data[i]}")
            print(f"  GL100:   {gl_data[i]}")
            break

# Check last frames
print(f"\nLast 5 frames of GL100 download:")
for i in range(-5, 0):
    print(f"  [{gl_data.shape[0] + i}] {gl_data[i]}")

print(f"\nCorresponding Windows GUI frames:")
start_idx = gl_data.shape[0] - 5
for i in range(5):
    print(f"  [{start_idx + i}] {win_data[start_idx + i]}")

# Calculate expected frames
print(f"\n" + "="*70)
print("EXPECTED vs ACTUAL")
print("="*70)
track_bytes = 264600
expected_frames = track_bytes // 6
print(f"Track bytes from device: {track_bytes:,}")
print(f"Expected frames (÷6): {expected_frames:,}")
print(f"Windows GUI frames: {win_data.shape[0]:,}")
print(f"GL100 frames: {gl_data.shape[0]:,}")
print(f"Missing: {expected_frames - gl_data.shape[0]:,}")
