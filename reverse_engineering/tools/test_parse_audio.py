#!/usr/bin/env python3
"""Test parse_audio_data function with known input."""

import sys
sys.path.insert(0, 'src')

from gl100.protocol import GL100Protocol
import numpy as np

# Create test data: 24-bit stereo interleaved
# Frame 0: L=0, R=0
# Frame 1: L=100, R=100
# Frame 2: L=1000, R=1000

test_data = bytearray()

# 12-byte header (track info)
test_data.extend([0x01, 0x00, 0x00, 0x00])  # exists
test_data.extend([36, 0, 0, 0])  # size = 36 bytes (12 samples, 6 frames)
test_data.extend([0x00, 0x00, 0x00, 0x00])  # padding

# Audio data (24-bit LE stereo interleaved)
# Frame 0: L=0, R=0
test_data.extend([0x00, 0x00, 0x00])  # L = 0
test_data.extend([0x00, 0x00, 0x00])  # R = 0

# Frame 1: L=100, R=100
test_data.extend([0x64, 0x00, 0x00])  # L = 100
test_data.extend([0x64, 0x00, 0x00])  # R = 100

# Frame 2: L=1000, R=1000
test_data.extend([0xE8, 0x03, 0x00])  # L = 1000
test_data.extend([0xE8, 0x03, 0x00])  # R = 1000

# Frame 3: L=-100, R=-100
test_data.extend([0x9C, 0xFF, 0xFF])  # L = -100 (0xFFFF9C in 24-bit)
test_data.extend([0x9C, 0xFF, 0xFF])  # R = -100

# Frame 4: L=8388607 (max 24-bit), R=8388607
test_data.extend([0xFF, 0xFF, 0x7F])  # L = 8388607
test_data.extend([0xFF, 0xFF, 0x7F])  # R = 8388607

# Frame 5: L=-8388608 (min 24-bit), R=-8388608
test_data.extend([0x00, 0x00, 0x80])  # L = -8388608
test_data.extend([0x00, 0x00, 0x80])  # R = -8388608

print(f"Test data size: {len(test_data)} bytes")
print(f"Expected: 12 byte header + 36 bytes audio = 48 bytes")

# Parse with header skip
audio = GL100Protocol.parse_audio_data(bytes(test_data), skip_header=True)

print(f"\nParsed audio:")
print(f"  Shape: {audio.shape}")
print(f"  Expected: (6, 2) for 6 frames, 2 channels")
print(f"  Dtype: {audio.dtype}")
print(f"  Values:")
print(audio)

# Expected values after conversion to int32:
# The function does: (val << 8) >> 8 << 8
# For val=100: 100 << 8 = 25600, >> 8 = 100, << 8 = 25600
# For val=1000: 1000 << 8 = 256000, >> 8 = 1000, << 8 = 256000
# etc.
