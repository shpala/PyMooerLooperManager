#!/usr/bin/env python3
"""Debug raw bytes to understand the mismatch."""

import sys
sys.path.insert(0, 'src')

from gl100.usb_device import GL100Device
import scipy.io.wavfile as wav
import numpy as np

device = GL100Device()
device.connect()

try:
    # Download first chunk
    print("Downloading first chunk...")
    cmd = device.protocol.create_download_command(4, chunk=0)
    device._write(cmd)
    chunk = device._read(size=1024, endpoint=0x83, timeout=5000)

    print(f"\nFirst chunk: {len(chunk)} bytes")
    print("\nFirst 64 bytes (hex):")
    for i in range(0, 64, 16):
        hex_str = ' '.join(f'{b:02x}' for b in chunk[i:i+16])
        ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk[i:i+16])
        print(f"  {i:04x}: {hex_str}  {ascii_str}")

    # Parse with current code
    print("\n" + "="*70)
    print("CURRENT PARSING (skip 16 bytes, then parse 24-bit)")
    print("="*70)
    audio = device.protocol.parse_audio_data(chunk, skip_header=True)
    print(f"Shape: {audio.shape}")
    print(f"First 5 frames: {audio[:5].tolist()}")

    # Try parsing starting at different offsets
    for offset in [0, 12, 16, 20]:
        print(f"\n" + "="*70)
        print(f"TESTING: Skip {offset} bytes")
        print("="*70)

        audio_bytes = chunk[offset:]
        num_frames = min(5, len(audio_bytes) // 6)  # Just first 5 frames
        trimmed = audio_bytes[:num_frames * 6]

        byte_array = np.frombuffer(trimmed, dtype=np.uint8).reshape(num_frames * 2, 3)
        samples = (
            byte_array[:, 0].astype(np.int32)
            | (byte_array[:, 1].astype(np.int32) << 8)
            | (byte_array[:, 2].astype(np.int32) << 16)
        )
        samples = (samples << 8) >> 8  # Sign extend
        samples = samples << 8  # Scale
        samples = samples.reshape(num_frames, 2)

        print(f"First {num_frames} frames: {samples.tolist()}")

        # Check if it matches Windows GUI
        _, win_data = wav.read("GL_LOOPFILE_04.wav")
        if num_frames > 0 and np.array_equal(samples, win_data[:num_frames]):
            print("✓ MATCHES Windows GUI!")
        elif num_frames > 0 and np.array_equal(samples[0], win_data[0]):
            print("✓ First frame matches!")
        else:
            print(f"Expected: {win_data[:num_frames].tolist()}")

finally:
    device.disconnect()
