#!/usr/bin/env python3
"""Test multiple chunks to see where the real audio data is."""

import sys
sys.path.insert(0, 'src')

from gl100.usb_device import GL100Device
import numpy as np

device = GL100Device()
device.connect()

try:
    # Test chunks: 0, 1, 10, 50, 100
    test_chunks = [0, 1, 10, 50, 100, 200]

    for chunk_idx in test_chunks:
        print(f"\n{'='*70}")
        print(f"CHUNK {chunk_idx}")
        print(f"{'='*70}")

        try:
            cmd = device.protocol.create_download_command(4, chunk=chunk_idx)
            device._write(cmd)
            chunk = device._read(size=1024, endpoint=0x83, timeout=2000)

            print(f"Received: {len(chunk)} bytes")

            # Show first 32 bytes
            print(f"First 32 bytes (hex):")
            for i in range(0, min(32, len(chunk)), 16):
                hex_str = ' '.join(f'{b:02x}' for b in chunk[i:i+16])
                print(f"  {i:04x}: {hex_str}")

            # Parse audio (skip 16 bytes for first chunk, 0 for others)
            skip = 16 if chunk_idx == 0 else 0
            audio_bytes = chunk[skip:]
            num_frames = len(audio_bytes) // 6

            if num_frames > 0:
                trimmed = audio_bytes[:num_frames * 6]
                byte_array = np.frombuffer(trimmed, dtype=np.uint8).reshape(num_frames * 2, 3)
                samples = (
                    byte_array[:, 0].astype(np.int32)
                    | (byte_array[:, 1].astype(np.int32) << 8)
                    | (byte_array[:, 2].astype(np.int32) << 16)
                )
                samples = (samples << 8) >> 8
                samples = samples << 8
                samples = samples.reshape(num_frames, 2)

                print(f"\nParsed {num_frames} frames:")
                print(f"  First 3: {samples[:3].tolist()}")
                print(f"  All zeros? {(samples == 0).all()}")
                print(f"  Non-zero count: {np.count_nonzero(samples)}")
                if np.count_nonzero(samples) > 0:
                    print(f"  Min/Max: {samples.min()} / {samples.max()}")

        except Exception as e:
            print(f"Error: {e}")

    print(f"\n{'='*70}")
    print("COMPARISON WITH WINDOWS GUI")
    print(f"{'='*70}")
    import scipy.io.wavfile as wav
    _, win_data = wav.read("GL_LOOPFILE_04.wav")
    print(f"Windows GUI first 5 frames: {win_data[:5].tolist()}")
    print(f"Windows GUI has non-zero data: {np.count_nonzero(win_data)} non-zero values")

finally:
    device.disconnect()
