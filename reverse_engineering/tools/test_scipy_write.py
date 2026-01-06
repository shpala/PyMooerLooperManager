#!/usr/bin/env python3
"""Test how scipy.io.wavfile handles int32 stereo arrays."""

import numpy as np
import scipy.io.wavfile as wav

# Create test data (6 frames, 2 channels, int32)
audio_stereo = np.array([[0, 0],
                         [25600, 25600],
                         [256000, 256000],
                         [-25600, -25600],
                         [2147483392, 2147483392],
                         [-2147483648, -2147483648]], dtype=np.int32)

print(f"Test stereo audio:")
print(f"  Shape: {audio_stereo.shape}")
print(f"  Dtype: {audio_stereo.dtype}")

# Write as WAV
wav.write("test_stereo.wav", 44100, audio_stereo)

# Read it back
rate, data = wav.read("test_stereo.wav")

print(f"\nRead back:")
print(f"  Rate: {rate}")
print(f"  Shape: {data.shape}")
print(f"  Dtype: {data.dtype}")
print(f"  Data: {data}")

# Check file properties
import subprocess
result = subprocess.run(['file', 'test_stereo.wav'], capture_output=True, text=True)
print(f"\nFile info: {result.stdout.strip()}")

# Now test with flattened array (mono)
audio_mono = audio_stereo.flatten()
print(f"\n\nTest mono (flattened) audio:")
print(f"  Shape: {audio_mono.shape}")
print(f"  Dtype: {audio_mono.dtype}")

wav.write("test_mono.wav", 44100, audio_mono)
rate, data = wav.read("test_mono.wav")

print(f"\nRead back:")
print(f"  Rate: {rate}")
print(f"  Shape: {data.shape}")
print(f"  Dtype: {data.dtype}")

result = subprocess.run(['file', 'test_mono.wav'], capture_output=True, text=True)
print(f"\nFile info: {result.stdout.strip()}")
