#!/usr/bin/env python3
"""Verify that our fix is correct by simulating what it would do"""

import numpy as np
import scipy.io.wavfile as wav
from gl100.protocol import GL100Protocol

# Load the Windows reference file
_, win_data = wav.read("GL_LOOPFILE_04.wav")
print("Windows reference file:")
print(f"  First 5 frames: {win_data[:5].tolist()}")

# Simulate what the device would send as first chunk:
# The device sends: [18-byte header][audio data]
# Let's create a fake first chunk with the header + audio that should decode to match Windows

# Convert first few frames of Windows data back to 24-bit format
protocol = GL100Protocol()

# The Windows file is int32 scaled by 256, so divide by 256 to get original 24-bit values
win_24bit = (win_data // 256).astype(np.int16)

# Encode to bytes (24-bit format)
encoded = protocol.encode_audio_data(win_24bit[:10])  # First 10 frames
print(f"\nEncoded first 10 frames to {len(encoded)} bytes (24-bit)")

# Create a simulated device response with 18-byte header
header = bytes(18)  # 18 zero bytes as header
simulated_response = header + encoded

print(f"\nSimulated device response: {len(simulated_response)} bytes")
print(f"  Header: {len(header)} bytes")
print(f"  Audio: {len(encoded)} bytes")

# Now parse it with skip_header=True (our current code)
parsed_with_skip = protocol.parse_audio_data(simulated_response, skip_header=True)
print(f"\nParsed with skip_header=True:")
print(f"  Shape: {parsed_with_skip.shape}")
print(f"  First 5 frames: {parsed_with_skip[:5].tolist()}")

# Parse it with skip_header=False (what would happen if we didn't skip)
parsed_without_skip = protocol.parse_audio_data(simulated_response, skip_header=False)
print(f"\nParsed with skip_header=False:")
print(f"  Shape: {parsed_without_skip.shape}")
print(f"  First 5 frames: {parsed_without_skip[:5].tolist()}")

# Compare
if np.array_equal(parsed_with_skip[:5], win_data[:5]):
    print("\n✓✓✓ skip_header=True produces CORRECT alignment!")
elif np.array_equal(parsed_without_skip[:5], win_data[:5]):
    print("\n✓✓✓ skip_header=False produces CORRECT alignment!")
else:
    print("\n✗ Neither matches - something else is wrong")
    print(f"\nExpected: {win_data[:5].tolist()}")
