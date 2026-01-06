#!/usr/bin/env python3
"""Test play command with detailed output"""

from gl100.usb_device import GL100Device
import logging

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

device = GL100Device()

try:
    print("Connecting to device...")
    if not device.connect():
        print("Failed to connect")
        exit(1)

    print("Connected!\n")

    # First, check which slots have tracks
    print("Checking track list...")
    tracks = device.list_tracks()

    occupied_slots = [t for t in tracks if t.has_track]
    print(f"\nFound {len(occupied_slots)} tracks:")
    for track in occupied_slots[:10]:  # Show first 10
        print(f"  Slot {track.slot}: {track.duration:.2f}s, {track.size:,} bytes")

    if not occupied_slots:
        print("\nNo tracks found! Upload a track first.")
        exit(1)

    # Try playing the first available track
    test_slot = occupied_slots[0].slot
    print(f"\nAttempting to play slot {test_slot}...")

    # Send play command
    cmd = device.protocol.create_play_command(test_slot)
    print(f"Play command: {cmd[:14].hex()}")
    device._write(cmd)
    print("Command sent successfully")

    # Try reading response on endpoint 0x81 (status)
    print("\nTrying to read response on endpoint 0x81...")
    try:
        response_81 = device._read(size=64, endpoint=0x81, timeout=1000)
        print(f"Response on 0x81: {response_81.hex()}")
    except Exception as e:
        print(f"No response on 0x81: {e}")

    # Try reading response on endpoint 0x83 (data)
    print("\nTrying to read response on endpoint 0x83...")
    try:
        response_83 = device._read(size=1024, endpoint=0x83, timeout=1000)
        print(f"Response on 0x83 ({len(response_83)} bytes):")
        print(f"  First 32 bytes: {response_83[:32].hex()}")
    except Exception as e:
        print(f"No response on 0x83: {e}")

    print("\n✓ Play command completed")
    print("Check if device is playing audio now...")

finally:
    device.disconnect()
    print("\nDisconnected")
