#!/usr/bin/env python3
"""Find the exact alignment between Windows and GL100 data."""

import scipy.io.wavfile as wav
import numpy as np

_, gl_data = wav.read("track_4.wav")
_, win_data = wav.read("GL_LOOPFILE_04.wav")

print("Searching for matching frames...\n")

# Check if any GL100 frames match any Windows frames
found = False
for gl_idx in range(min(20, len(gl_data))):
    for win_idx in range(min(20, len(win_data))):
        if np.array_equal(gl_data[gl_idx], win_data[win_idx]):
            print(f"✓ GL100 frame {gl_idx} matches Windows frame {win_idx}")
            print(f"  GL100[{gl_idx}] = {gl_data[gl_idx].tolist()}")
            print(f"  Windows[{win_idx}] = {win_data[win_idx].tolist()}")
            if gl_idx == 0:
                print(f"  → We're skipping {win_idx} frames too many = {win_idx * 8} bytes in WAV")
            found = True
            break
    if found:
        break

if not found:
    print("No matching frames found in first 20 frames.")
    print("\nLet's check the raw bytes instead...")

    win_bytes = win_data.tobytes()
    gl_bytes = gl_data.tobytes()

    # Search for first 16 bytes of Windows data in GL100 data
    win_pattern = win_bytes[:16]

    for offset in range(min(200, len(gl_bytes) - 16)):
        if gl_bytes[offset:offset+16] == win_pattern:
            print(f"\n✓ Windows bytes [0:16] found at GL100 byte offset {offset}")
            print(f"  This is {offset // 8} frames into GL100 data")
            print(f"  We're reading {offset} bytes too early")
            break

    # Also search for GL100's first bytes in Windows data
    gl_pattern = gl_bytes[:16]

    for offset in range(min(200, len(win_bytes) - 16)):
        if win_bytes[offset:offset+16] == gl_pattern:
            print(f"\n✓ GL100 bytes [0:16] found at Windows byte offset {offset}")
            print(f"  This is {offset // 8} frames into Windows data")
            print(f"  We're skipping {offset} bytes too many")
            break

print("\n" + "="*70)
print("First 10 frames comparison:")
print("="*70)
for i in range(10):
    match = "✓" if np.array_equal(gl_data[i], win_data[i]) else "✗"
    print(f"{match} Frame {i}: GL100={gl_data[i].tolist()}, Win={win_data[i].tolist()}")
