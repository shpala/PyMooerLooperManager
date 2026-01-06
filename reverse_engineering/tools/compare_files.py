#!/usr/bin/env python3
"""Compare the two files in detail."""

import scipy.io.wavfile as wav
import numpy as np

# Read both files
print("GL_LOOPFILE_04.wav (Windows GUI):")
rate1, data1 = wav.read("GL_LOOPFILE_04.wav")
print(f"  Shape: {data1.shape}")
print(f"  Duration: {data1.shape[0] / rate1:.3f} seconds")
print(f"  Bytes: {data1.nbytes:,}")
print(f"  First 5 frames:")
print(f"    {data1[:5]}")

print("\ntrack_4_fix.wav (GL100 project):")
rate2, data2 = wav.read("track_4_fix.wav")
print(f"  Shape: {data2.shape}")
print(f"  Duration: {data2.shape[0] / rate2:.3f} seconds")
print(f"  Bytes: {data2.nbytes:,}")
print(f"  First 5 frames:")
print(f"    {data2[:5]}")

print("\nDifference:")
print(f"  Missing frames: {data1.shape[0] - data2.shape[0]}")
print(f"  Missing bytes: {data1.nbytes - data2.nbytes:,}")
print(f"  Missing duration: {(data1.shape[0] - data2.shape[0]) / rate1:.3f} seconds")

# Check if the data that exists matches
if data2.shape[0] > 0:
    overlap = min(data1.shape[0], data2.shape[0])
    print(f"\nComparing first {overlap} frames:")
    print(f"  Arrays equal: {np.array_equal(data1[:overlap], data2[:overlap])}")
    print(f"  Max difference: {np.max(np.abs(data1[:overlap] - data2[:overlap]))}")

    # Find first difference
    if not np.array_equal(data1[:overlap], data2[:overlap]):
        diffs = np.where(data1[:overlap] != data2[:overlap])
        if len(diffs[0]) > 0:
            first_diff = diffs[0][0]
            print(f"  First difference at frame {first_diff}:")
            print(f"    Windows GUI: {data1[first_diff]}")
            print(f"    Downloaded:  {data2[first_diff]}")
