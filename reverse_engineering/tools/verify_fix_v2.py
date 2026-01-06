#!/usr/bin/env python3
"""Verify the fix with proper 24-bit encoding"""

import numpy as np
import scipy.io.wavfile as wav
from gl100.protocol import GL100Protocol

# Load Windows reference
_, win_data = wav.read("GL_LOOPFILE_04.wav")
print("Windows reference:")
print(f"  First 3 frames: {win_data[:3].tolist()}")

# The device transmits 24-bit audio (int32 values right-shifted 8 bits)
# Convert Windows int32 data back to 24-bit representation
win_24bit = win_data >> 8  # Remove the scaling

# Manually encode first 3 frames to 24-bit bytes (what device sends)
audio_bytes = bytearray()
for frame in win_24bit[:3]:
    for sample in frame:
        # Convert int32 to 24-bit little-endian
        # Handle negative numbers with two's complement
        if sample < 0:
            sample = (1 << 24) + sample  # Two's complement
        audio_bytes.extend([
            sample & 0xFF,
            (sample >> 8) & 0xFF,
            (sample >> 16) & 0xFF
        ])

print(f"\n24-bit encoded: {len(audio_bytes)} bytes (3 frames × 2 channels × 3 bytes = 18 bytes)")
print(f"  Hex: {audio_bytes.hex()}")

# Test with 18-byte header + audio
header = bytes(18)
with_header = header + bytes(audio_bytes)

print(f"\nWith header: {len(with_header)} bytes")

# Parse with skip_header=True
protocol = GL100Protocol()
parsed_skip = protocol.parse_audio_data(with_header, skip_header=True)
print(f"\nParsed with skip_header=True:")
print(f"  Shape: {parsed_skip.shape}")
print(f"  Values: {parsed_skip.tolist()}")

# Parse with skip_header=False  
parsed_no_skip = protocol.parse_audio_data(with_header, skip_header=False)
print(f"\nParsed with skip_header=False:")
print(f"  Shape: {parsed_no_skip.shape}")
print(f"  First 3: {parsed_no_skip[:3].tolist()}")

# Check which matches
if np.array_equal(parsed_skip, win_data[:3]):
    print("\n✓✓✓ skip_header=True is CORRECT!")
elif np.array_equal(parsed_no_skip[:3], win_data[:3]):
    print("\n✓✓✓ skip_header=False is CORRECT!")
else:
    print("\n✗ Neither matches")
    print(f"Expected: {win_data[:3].tolist()}")
