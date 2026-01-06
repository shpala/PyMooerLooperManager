#!/usr/bin/env python3
"""Analyze the raw device response to find the correct size field."""

import struct

# Raw response from diagnose_size.py
hex_str = "01000100109eba03000000000a00850300000000000000000000000000000000"
data = bytes.fromhex(hex_str)

print("GL100 Response Analysis")
print("=" * 70)
print(f"Raw hex: {hex_str}")
print(f"Length: {len(data)} bytes")
print()

# Known facts:
# - Slot 0 has audio
# - Actual file size should be ~83.4 MB = 87,465,984 bytes
# - Device shows 59.66 MB in UI

target_size = 83_415_788  # Actual file size (79.55 MB)

print("Testing different byte positions as 32-bit little-endian integers:")
print("-" * 70)

for offset in range(len(data) - 3):
    value = struct.unpack("<I", data[offset:offset+4])[0]
    if value > 1000000:  # Only show values > 1MB
        mb = value / (1024**2)
        ratio = value / target_size if target_size > 0 else 0
        match = "★ MATCH!" if abs(ratio - 1.0) < 0.05 else ""
        print(f"  Offset {offset:2d}: {value:12,} bytes = {mb:7.2f} MB  (ratio: {ratio:.3f}) {match}")

print()
print("=" * 70)
print("Testing if size needs conversion:")
print("-" * 70)

# Current interpretation (bytes 4-7)
current = 62_561_808
print(f"Current (bytes 4-7): {current:,} bytes = {current/(1024**2):.2f} MB")
print()

# Try various conversions
conversions = [
    ("Multiply by 4/3", current * 4 / 3),
    ("Multiply by 3/2", current * 3 / 2),
    ("Multiply by 1.4", current * 1.4),
    ("Multiply by 2", current * 2),
]

for name, result in conversions:
    ratio = result / target_size
    match = "★ MATCH!" if abs(ratio - 1.0) < 0.05 else ""
    print(f"  {name:20s}: {result:12,.0f} bytes = {result/(1024**2):7.2f} MB  (ratio: {ratio:.3f}) {match}")

print()
print("=" * 70)
