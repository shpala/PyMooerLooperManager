#!/usr/bin/env python3
"""Properly calculate how many chunks we need to download."""

track_size_bytes = 264600
total_frames_needed = track_size_bytes // 6  # 44,100 frames

print(f"Track info:")
print(f"  Device reports: {track_size_bytes:,} bytes")
print(f"  Total frames needed: {total_frames_needed:,}")

# First chunk
first_chunk_audio_bytes = 1024 - 16  # 1008 bytes
first_chunk_frames = first_chunk_audio_bytes // 6  # 168 frames
print(f"\nFirst chunk (chunk 0):")
print(f"  Audio bytes: {first_chunk_audio_bytes}")
print(f"  Frames: {first_chunk_frames}")

# Remaining frames
remaining_frames = total_frames_needed - first_chunk_frames
print(f"\nRemaining:")
print(f"  Frames still needed: {remaining_frames:,}")

# Subsequent chunks
bytes_per_subsequent_chunk = 1024
frames_per_subsequent_chunk = bytes_per_subsequent_chunk // 6  # 170 frames
bytes_used_per_chunk = frames_per_subsequent_chunk * 6  # 1020 bytes (4 discarded)

print(f"\nSubsequent chunks:")
print(f"  Raw chunk size: {bytes_per_subsequent_chunk} bytes")
print(f"  Usable frames per chunk: {frames_per_subsequent_chunk}")
print(f"  Bytes used per chunk: {bytes_used_per_chunk} (4 discarded)")

# Calculate how many additional chunks needed
import math
num_additional_chunks_needed = math.ceil(remaining_frames / frames_per_subsequent_chunk)

print(f"\nChunk calculation:")
print(f"  Additional chunks needed: {num_additional_chunks_needed}")
print(f"  Total chunks: {1 + num_additional_chunks_needed}")

# Verify
frames_from_subsequent_chunks = num_additional_chunks_needed * frames_per_subsequent_chunk
total_frames_downloaded = first_chunk_frames + frames_from_subsequent_chunks

print(f"\nVerification:")
print(f"  Frames from first chunk: {first_chunk_frames}")
print(f"  Frames from subsequent chunks: {frames_from_subsequent_chunks}")
print(f"  Total frames downloaded: {total_frames_downloaded:,}")
print(f"  Target frames: {total_frames_needed:,}")
print(f"  Match: {total_frames_downloaded >= total_frames_needed}")
print(f"  Extra frames: {total_frames_downloaded - total_frames_needed}")

# Current (wrong) calculation in code
remaining_bytes = track_size_bytes - first_chunk_audio_bytes
num_additional_chunks_wrong = (remaining_bytes + 1023) // 1024

print(f"\n" + "="*60)
print(f"Current code calculation (WRONG):")
print(f"  Remaining bytes: {remaining_bytes:,}")
print(f"  Additional chunks: {num_additional_chunks_wrong}")
print(f"  Would download frames: {first_chunk_frames + num_additional_chunks_wrong * frames_per_subsequent_chunk:,}")
print(f"  Shortage: {total_frames_needed - (first_chunk_frames + num_additional_chunks_wrong * frames_per_subsequent_chunk)}")
