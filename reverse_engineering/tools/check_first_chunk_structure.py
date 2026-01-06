#!/usr/bin/env python3
"""Check what's actually in the first chunk."""

# From earlier test_download_bytes.py output:
# First chunk header was: 01 00 01 00 98 09 04 00 00 00 00 00 0a 00 85 03

first_chunk_header_hex = "01 00 01 00 98 09 04 00 00 00 00 00 0a 00 85 03"
header_bytes = bytes.fromhex(first_chunk_header_hex)

print("First 16 bytes of download chunk:")
print(f"  Hex: {first_chunk_header_hex}")

# Our code reads this as "track info":
track_exists = header_bytes[0] == 0x01
import struct
track_size = struct.unpack("<I", header_bytes[4:8])[0]

print(f"\nWhat we're currently reading (WRONG):")
print(f"  Byte 0 as 'track_exists': {track_exists}")
print(f"  Bytes 4-7 as 'track_size': {track_size:,} bytes")

print(f"\nBut these are actually PROTOCOL HEADER bytes!")
print(f"  The track size should come from the LIST command,")
print(f"  NOT from the download chunks!")

print(f"\nWhat should happen:")
print(f"  1. Call LIST command to get track size for all slots")
print(f"  2. Use that size to calculate chunks needed")
print(f"  3. Download chunks contain ONLY protocol header + audio")
print(f"  4. First chunk: bytes 0-15 are protocol header")
print(f"  5. First chunk: bytes 16+ are AUDIO (not track info!)")
