# GL100 USB Protocol Reverse Engineering Report

This document covers the reverse-engineering of the USB protocol used by the Mooer GL series looper pedals (GL100, GL200).

## Methodology

The protocol was identified through USB packet capture using Wireshark and USBPcap to monitor the official Windows application. Binary analysis of the official executable (mooer.exe) confirmed it's an Electron application using Chrome's USB API for bulk transfers. Command structures and checksum algorithms were verified through iterative testing with Python and PyUSB.

## USB Configuration

The device uses vendor ID 0x34DB (Mooer Corporation) and product ID 0x0008 (GL100). Three endpoints handle communication:
- 0x02 (OUT): Host-to-device commands
- 0x81 (IN): Device-to-host status and acknowledgments
- 0x83 (IN): Device-to-host data transfers (audio and track info)

## Command Protocol

All commands are 64-byte packets.

### Packet Structure

| Offset | Size | Description |
| :--- | :--- | :--- |
| 0x00 | 3 | Static Header: `0x3F 0xAA 0x55` |
| 0x03 | 1 | Command Type (e.g., `0x07` for Track Ops) |
| 0x04 | 1 | Padding (`0x00`) |
| 0x05 | 1 | Subcommand |
| 0x06 | 2 | Argument 1 (Slot number or other) |
| 0x08 | 2 | Argument 2 (Chunk Index for transfers) |
| 0x0C | 2 | CRC-16 Checksum (Big-endian) |
| 0x0E | 50 | Zero Padding |

**CRC-16**: Uses a table-based algorithm (XModem style) calculated over bytes 3 through 11.

### Command Types

Byte 3 of the packet header defines the primary command category:

| Value | Name | Description |
| :--- | :--- | :--- |
| `0x01` | Init Upload | Used to initialize an upload sequence (Subcommand `0x86`). |
| `0x03` | Delete Ops | Used specifically for delete operations (often paired with Subcommand `0x88`). |
| `0x07` | Track Ops | The primary command type for most functions (List, Download, Upload Data, Play). |

## Core Operations

### 1. List/Query Tracks
Command type 0x07, subcommand 0x82 (download), chunk 0. Requesting chunk 0 of any slot returns a metadata header on endpoint 0x83. Byte 0 is the status (0x01 = has track, 0x00 = empty). Bytes 4-7 contain the track size in bytes (32-bit little-endian).

### 2. Download Track
Audio data starts at chunk 1. Chunk size is 1024 bytes. Important: chunks are not aligned to 6-byte audio frames (1024 % 6 = 4), so a buffer must accumulate the 4-byte remainders to maintain channel alignment.

### 3. Upload Track
Requires an initialization command (type 0x01, sub 0x86). Chunk 0 must contain the track size in the first 4 bytes. Audio data follows starting at chunk 1 on endpoint 0x03.

### 4. Play/Stop
Command type 0x07, subcommand 0x8A. Action byte at offset 6: 0x01 for play, 0x00 for stop.

## Audio Format

The device operates with raw PCM data: 44100 Hz sample rate, 24-bit signed integers (3 bytes per sample), 2 channels (stereo, interleaved), 6-byte frame size. Mono files are converted to stereo with -3dB attenuation (scaling factor ≈ 0.7071) to maintain constant perceived power.
