#!/usr/bin/env python3
"""Analyze WAV file formats to debug the stereo/mono issue."""

import numpy as np
import scipy.io.wavfile as wav

# Read both files
print("Reading GL_LOOPFILE_04.wav (Windows GUI - correct)...")
rate1, data1 = wav.read("GL_LOOPFILE_04.wav")
print(f"  Sample rate: {rate1} Hz")
print(f"  Data shape: {data1.shape}")
print(f"  Data dtype: {data1.dtype}")
print(f"  Data min/max: {data1.min()}/{data1.max()}")
print(f"  First 10 samples:\n{data1[:10]}")

print("\nReading track_4.wav (GL100 project - incorrect)...")
rate2, data2 = wav.read("track_4.wav")
print(f"  Sample rate: {rate2} Hz")
print(f"  Data shape: {data2.shape}")
print(f"  Data dtype: {data2.dtype}")
print(f"  Data min/max: {data2.min()}/{data2.max()}")
print(f"  First 10 samples:\n{data2[:10]}")

print("\nReading out24bit.wav (original uploaded)...")
rate3, data3 = wav.read("out24bit.wav")
print(f"  Sample rate: {rate3} Hz")
print(f"  Data shape: {data3.shape}")
print(f"  Data dtype: {data3.dtype}")
print(f"  Data min/max: {data3.min()}/{data3.max()}")
print(f"  First 10 samples:\n{data3[:10]}")
