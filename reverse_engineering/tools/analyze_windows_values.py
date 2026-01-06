#!/usr/bin/env python3
"""Analyze what the Windows GUI values represent."""

import scipy.io.wavfile as wav
import numpy as np

_, win_data = wav.read("GL_LOOPFILE_04.wav")

print("Windows GUI values analysis:")
print(f"\nFirst 5 frames (int32):")
for i in range(5):
    L, R = win_data[i]
    L_hex = L if L >= 0 else (1 << 32) + L
    R_hex = R if R >= 0 else (1 << 32) + R
    print(f"  [{i}] L={L:12d} (0x{L_hex:08x})  R={R:12d} (0x{R_hex:08x})")

# Check if these are scaled 24-bit values
print(f"\nDividing by 256 (removing 8-bit scaling):")
for i in range(5):
    L, R = win_data[i]
    L_24 = L >> 8
    R_24 = R >> 8
    print(f"  [{i}] L={L_24:8d} (0x{L_24 & 0xFFFFFF:06x})  R={R_24:8d} (0x{R_24 & 0xFFFFFF:06x})")

# Check last frames
print(f"\nLast 5 frames (int32):")
for i in range(-5, 0):
    L, R = win_data[i]
    L_hex = L if L >= 0 else (1 << 32) + L
    R_hex = R if R >= 0 else (1 << 32) + R
    print(f"  [{len(win_data)+i}] L={L:12d} (0x{L_hex:08x})  R={R:12d} (0x{R_hex:08x})")

print(f"\nLast 5 frames divided by 256:")
for i in range(-5, 0):
    L, R = win_data[i]
    L_24 = L >> 8
    R_24 = R >> 8
    print(f"  [{len(win_data)+i}] L={L_24:8d} (0x{L_24 & 0xFFFFFF:06x})  R={R_24:8d} (0x{R_24 & 0xFFFFFF:06x})")

# Pattern check
print(f"\nPattern check (looking for symmetry):")
print(f"  First L: {win_data[0, 0]}, Last R: {win_data[-1, 1]}")
print(f"  First R: {win_data[0, 1]}, Last L: {win_data[-1, 0]}")
print(f"  Sum: {win_data[0, 0] + win_data[-1, 1]}")
