#!/usr/bin/env python3
"""Test script to verify track durations are calculated correctly."""

import sys
sys.path.insert(0, '/home/shpala/dev/gl100/src')

from gl100.usb_device import GL100Device

def format_duration(seconds):
    """Format duration as mm:ss."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"

def main():
    device = GL100Device()

    print("Connecting to GL100...")
    if not device.connect():
        print("Failed to connect")
        return

    print("Querying tracks 0-3...\n")

    try:
        tracks = device.list_tracks()

        for slot in range(4):
            track = tracks[slot]
            if track.has_track:
                duration_str = format_duration(track.duration)
                print(f"Length of the {slot} track is {duration_str}")
                print(f"  (Raw: {track.duration:.2f} seconds, {track.size} bytes)")
            else:
                print(f"Track {slot}: Empty")

    finally:
        device.disconnect()

if __name__ == "__main__":
    main()
