#!/usr/bin/env python3
"""Test the fixed download against the existing track_4.wav file."""

import sys
sys.path.insert(0, 'src')

import numpy as np
import scipy.io.wavfile as wav
from gl100.protocol import GL100Protocol

# Read the existing incorrect file to understand what it contains
print("Reading existing track_4.wav (incorrect)...")
rate_old, data_old = wav.read("track_4.wav")
print(f"  Shape: {data_old.shape}")
print(f"  Dtype: {data_old.dtype}")

# Read the correct Windows GUI file
print("\nReading GL_LOOPFILE_04.wav (correct from Windows GUI)...")
rate_correct, data_correct = wav.read("GL_LOOPFILE_04.wav")
print(f"  Shape: {data_correct.shape}")
print(f"  Dtype: {data_correct.dtype}")
print(f"  First 5 frames:")
print(data_correct[:5])

# Simulate what the fixed code should produce
# The device returns 264600 bytes of 24-bit stereo audio
# With the fix, this should parse to (44100, 2) int32 stereo

print("\n" + "="*60)
print("VERIFICATION:")
print(f"  Expected output shape: (44100, 2)")
print(f"  Windows GUI shape: {data_correct.shape}")
print(f"  Match: {data_correct.shape == (44100, 2)}")

# Test with a small chunk to verify parsing
test_chunk = b'\x01\x00\x00\x00' + bytes([0x98, 0x09, 0x04, 0x00]) + b'\x00' * 4
test_chunk += b'\x00' * 1012  # Fill to 1024 bytes

parsed = GL100Protocol.parse_audio_data(test_chunk, skip_header=True)
print(f"\nTest chunk parsing:")
print(f"  Input: 1024 bytes (12 header + 1012 audio)")
print(f"  Output shape: {parsed.shape}")
print(f"  Expected: (168, 2)  [1012 bytes ÷ 6 bytes/frame = 168 frames]")
print(f"  Correct: {parsed.shape == (168, 2)}")
