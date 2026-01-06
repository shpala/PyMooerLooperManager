#!/usr/bin/env python3
"""Find where GL100's bytes appear in Windows data."""

import scipy.io.wavfile as wav

_, win_data = wav.read("GL_LOOPFILE_04.wav")
_, gl_data = wav.read("track_4.wav")

win_bytes = win_data.tobytes()
gl_bytes = gl_data.tobytes()

print("Searching for GL100 pattern in Windows data...\n")

# Take first 32 bytes of GL100
gl_pattern = gl_bytes[:32]

print(f"GL100 pattern (first 32 bytes):")
for i in range(0, 32, 16):
    hex_str = ' '.join(f'{gl_pattern[i+j]:02x}' for j in range(16))
    print(f"  {i:04x}: {hex_str}")

print(f"\nSearching in Windows data...")

# Search for this pattern in Windows
found_offset = -1
for offset in range(len(win_bytes) - 32):
    if win_bytes[offset:offset+32] == gl_pattern:
        found_offset = offset
        print(f"\n✓ EXACT MATCH at offset {offset} bytes ({offset//8} frames)")
        break

if found_offset == -1:
    print("\nNo exact match found. Trying partial matches...")

    # Try to find best match (most matching bytes)
    best_offset = -1
    best_match_count = 0

    for offset in range(min(1000, len(win_bytes) - 32)):  # Check first 1000 bytes
        match_count = sum(1 for i in range(32) if win_bytes[offset + i] == gl_pattern[i])
        if match_count > best_match_count:
            best_match_count = match_count
            best_offset = offset

    print(f"\nBest partial match: offset {best_offset} ({best_match_count}/32 bytes match)")
    print(f"\nWindows at offset {best_offset}:")
    for i in range(0, 32, 16):
        hex_str = ' '.join(f'{win_bytes[best_offset+i+j]:02x}' for j in range(16))
        print(f"  {i:04x}: {hex_str}")

    print(f"\nGL100 (reference):")
    for i in range(0, 32, 16):
        hex_str = ' '.join(f'{gl_pattern[i+j]:02x}' for j in range(16))
        print(f"  {i:04x}: {hex_str}")

# Also check if GL100 is byte-shifted version of Windows
print(f"\n{'='*70}")
print("CHECKING FOR BYTE-LEVEL SHIFTS")
print(f"{'='*70}")

# The issue might be that we're off by N bytes in PARSING, not in the data
# So check if Windows[0] matches GL100[N] for some N

for shift in range(1, 20):
    if win_bytes[:100] == gl_bytes[shift:shift+100]:
        print(f"\n✓ Windows[0:100] == GL100[{shift}:{shift+100}]")
        print(f"  → GL100 data is shifted RIGHT by {shift} bytes")
        break
    elif win_bytes[shift:shift+100] == gl_bytes[:100]:
        print(f"\n✓ Windows[{shift}:{shift+100}] == GL100[0:100]")
        print(f"  → GL100 data is shifted LEFT by {shift} bytes (Windows offset)")
        print(f"  → We're starting to read {shift} bytes TOO EARLY")
        break
