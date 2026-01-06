#!/usr/bin/env python3
"""Compare the final downloaded file with Windows GUI file."""

import scipy.io.wavfile as wav
import numpy as np

print("Loading files...")
rate1, win_data = wav.read("GL_LOOPFILE_04.wav")
rate2, gl_data = wav.read("track_4.wav")

print("\n" + "="*70)
print("FILE COMPARISON")
print("="*70)

print(f"\nWindows GUI (GL_LOOPFILE_04.wav):")
print(f"  Sample rate: {rate1} Hz")
print(f"  Shape: {win_data.shape}")
print(f"  Dtype: {win_data.dtype}")
print(f"  Data bytes: {win_data.nbytes:,}")

print(f"\nGL100 Download (track_4.wav):")
print(f"  Sample rate: {rate2} Hz")
print(f"  Shape: {gl_data.shape}")
print(f"  Dtype: {gl_data.dtype}")
print(f"  Data bytes: {gl_data.nbytes:,}")

print(f"\n" + "="*70)
print("CONTENT COMPARISON")
print("="*70)

if win_data.shape == gl_data.shape:
    print(f"✓ Shapes match: {win_data.shape}")
else:
    print(f"✗ Shape mismatch!")
    print(f"  Windows: {win_data.shape}")
    print(f"  GL100:   {gl_data.shape}")

if rate1 == rate2:
    print(f"✓ Sample rates match: {rate1} Hz")
else:
    print(f"✗ Sample rate mismatch: {rate1} vs {rate2}")

# Check if data is identical
if np.array_equal(win_data, gl_data):
    print(f"✓ Audio data is IDENTICAL!")
    print(f"\n{'='*70}")
    print("SUCCESS: Files match perfectly!")
    print(f"{'='*70}")
else:
    print(f"✗ Audio data differs")

    # Find differences
    diff_mask = win_data != gl_data
    num_diffs = np.sum(diff_mask)
    total_values = win_data.size

    print(f"\nDifference statistics:")
    print(f"  Different values: {num_diffs:,} / {total_values:,} ({100*num_diffs/total_values:.4f}%)")

    # Find first difference
    diff_indices = np.where(diff_mask)
    if len(diff_indices[0]) > 0:
        first_diff_frame = diff_indices[0][0]
        first_diff_channel = diff_indices[1][0]

        print(f"\nFirst difference:")
        print(f"  Frame {first_diff_frame}, Channel {first_diff_channel}")
        print(f"  Windows: {win_data[first_diff_frame, first_diff_channel]}")
        print(f"  GL100:   {gl_data[first_diff_frame, first_diff_channel]}")

        print(f"\nContext around first difference (frame {first_diff_frame}):")
        start = max(0, first_diff_frame - 2)
        end = min(len(win_data), first_diff_frame + 3)

        print(f"  Windows GUI:")
        for i in range(start, end):
            marker = " <--" if i == first_diff_frame else ""
            print(f"    [{i}] {win_data[i]}{marker}")

        print(f"  GL100 Download:")
        for i in range(start, end):
            marker = " <--" if i == first_diff_frame else ""
            print(f"    [{i}] {gl_data[i]}{marker}")

    # Check if it's just a value difference or structural
    max_diff = np.max(np.abs(win_data.astype(np.int64) - gl_data.astype(np.int64)))
    print(f"\nMaximum absolute difference: {max_diff}")

# Show first and last few frames regardless
print(f"\n" + "="*70)
print("SAMPLE DATA")
print("="*70)

print(f"\nFirst 5 frames:")
print(f"  Windows: {win_data[:5].tolist()}")
print(f"  GL100:   {gl_data[:5].tolist()}")

print(f"\nLast 5 frames:")
print(f"  Windows: {win_data[-5:].tolist()}")
print(f"  GL100:   {gl_data[-5:].tolist()}")
