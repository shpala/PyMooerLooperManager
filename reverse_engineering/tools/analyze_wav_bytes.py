#!/usr/bin/env python3
"""Analyze the actual bytes in the downloaded WAV file."""

import scipy.io.wavfile as wav
import numpy as np

# Read both files
_, win_data = wav.read("GL_LOOPFILE_04.wav")
_, gl_data = wav.read("track_4.wav")

print("Analyzing byte-level differences...\n")

# Convert to bytes
win_bytes = win_data.tobytes()
gl_bytes = gl_data.tobytes()

print(f"Windows GUI bytes: {len(win_bytes):,}")
print(f"GL100 bytes:       {len(gl_bytes):,}")

# Show first 64 bytes
print(f"\nFirst 64 bytes comparison:")
print("\nWindows GUI (hex):")
for i in range(0, 64, 16):
    hex_str = ' '.join(f'{win_bytes[i+j]:02x}' for j in range(16))
    print(f"  {i:04x}: {hex_str}")

print("\nGL100 Download (hex):")
for i in range(0, 64, 16):
    hex_str = ' '.join(f'{gl_bytes[i+j]:02x}' for j in range(16))
    print(f"  {i:04x}: {hex_str}")

# Parse first frame manually from each
print("\n" + "="*70)
print("MANUAL PARSING OF FIRST FRAME")
print("="*70)

# Windows GUI - first frame (8 bytes for stereo int32)
win_L = int.from_bytes(win_bytes[0:4], byteorder='little', signed=True)
win_R = int.from_bytes(win_bytes[4:8], byteorder='little', signed=True)
print(f"\nWindows GUI frame 0:")
print(f"  Bytes [0-3]: {' '.join(f'{win_bytes[i]:02x}' for i in range(4))} = {win_L}")
print(f"  Bytes [4-7]: {' '.join(f'{win_bytes[i]:02x}' for i in range(4,8))} = {win_R}")

gl_L = int.from_bytes(gl_bytes[0:4], byteorder='little', signed=True)
gl_R = int.from_bytes(gl_bytes[4:8], byteorder='little', signed=True)
print(f"\nGL100 Download frame 0:")
print(f"  Bytes [0-3]: {' '.join(f'{gl_bytes[i]:02x}' for i in range(4))} = {gl_L}")
print(f"  Bytes [4-7]: {' '.join(f'{gl_bytes[i]:02x}' for i in range(4,8))} = {gl_R}")

# Analyze the relationship
print("\n" + "="*70)
print("RELATIONSHIP ANALYSIS")
print("="*70)

# Check if GL100 values are bit-shifted versions of Windows values
for shift in range(-16, 17):
    if shift == 0:
        continue

    if shift > 0:
        test_L = win_L << shift
        test_R = win_R << shift
        op = f"<< {shift}"
    else:
        test_L = win_L >> (-shift)
        test_R = win_R >> (-shift)
        op = f">> {-shift}"

    # Mask to 32-bit
    test_L = test_L if test_L >= -(1<<31) and test_L < (1<<31) else (test_L & 0xFFFFFFFF) - (1<<32) if test_L < 0 else test_L & 0xFFFFFFFF
    test_R = test_R if test_R >= -(1<<31) and test_R < (1<<31) else (test_R & 0xFFFFFFFF) - (1<<32) if test_R < 0 else test_R & 0xFFFFFFFF

    if test_L == gl_L and test_R == gl_R:
        print(f"MATCH FOUND: GL100 = Windows {op}")
        break

# Check second frame (should have non-zero values)
print("\n" + "="*70)
print("SECOND FRAME ANALYSIS")
print("="*70)

win_L2 = int.from_bytes(win_bytes[8:12], byteorder='little', signed=True)
win_R2 = int.from_bytes(win_bytes[12:16], byteorder='little', signed=True)
gl_L2 = int.from_bytes(gl_bytes[8:12], byteorder='little', signed=True)
gl_R2 = int.from_bytes(gl_bytes[12:16], byteorder='little', signed=True)

print(f"\nWindows GUI frame 1: L={win_L2}, R={win_R2}")
print(f"GL100 Download frame 1: L={gl_L2}, R={gl_R2}")

if win_L2 != 0:
    ratio_L = gl_L2 / win_L2 if win_L2 != 0 else 0
    ratio_R = gl_R2 / win_R2 if win_R2 != 0 else 0
    print(f"Ratio: L={ratio_L:.6f}, R={ratio_R:.6f}")

    # Check if it's a power of 2
    import math
    if ratio_L != 0:
        log2_L = math.log2(abs(ratio_L))
        print(f"Log2(ratio): {log2_L:.6f}")
        if abs(log2_L - round(log2_L)) < 0.01:
            print(f"GL100 appears to be Windows × 2^{round(log2_L)}")
