# GL100 USB Protocol Documentation

This document describes the USB protocol for the Mooer GL100 looper pedal, reverse-engineered from packet captures.

## USB Configuration

The device uses a vendor-specific interface class with three endpoints:
- 0x02 (OUT): Host to device commands
- 0x81 (IN): Device to host status/acknowledgments
- 0x83 (IN): Device to host data (audio, track info)

## Packet Structure

### Command Packet Format

All commands start with a common header:

```
Offset  Size  Description
------  ----  -----------
0x00    2     Command header (0xAA 0x55)
0x02    1     Command type
0x03    1     Reserved (0x00)
0x04    1     Subcommand
0x05    1     Slot number (0-99)
0x06    ...   Command-specific payload
```

### Command Types

| Value | Description |
|-------|-------------|
| 0x03  | Delete operation |
| 0x07  | Track operations |

### Subcommands (for 0x07 Track Operations)

| Value | Description |
|-------|-------------|
| 0x01  | Play/pause track |
| 0x03  | Delete track |
| 0x07  | Track metadata |
| 0x82  | Download track data |
| 0x88  | List all tracks |
| 0x89  | Upload track data |

## Command Details

### List Tracks

Request:
```
AA 55 07 00 88 00 00 00 ...
```

Response (endpoint 0x83):
Returns metadata for all 100 track slots. Format is a 16-byte header followed by 100 track entries of 8 bytes each:
- Byte 0: Status (0x00 = empty, 0x01 = has track)
- Bytes 1-3: Unknown/padding
- Bytes 4-7: Track size (little-endian 32-bit)

Important: The size value must be multiplied by 4/3 to get the actual audio data size in bytes. For example, if the device reports 62,561,808 bytes, the actual file size is 83,415,744 bytes. This 4:3 conversion factor has been verified empirically but the reason is unclear—could be internal compression, storage format representation, or just a protocol quirk.

### Download Track

Request:
```
AA 55 07 00 82 [SLOT] [CHUNK_LO] [CHUNK_HI] ...
```

SLOT is the track slot (0-99). CHUNK_LO and CHUNK_HI form a little-endian 16-bit chunk number for multi-packet transfers.

Response (endpoint 0x83):
Audio data comes back in chunks. The audio format is 44100 Hz, 24-bit signed integer, 2 channels (stereo), little-endian PCM with interleaved L, R, L, R samples.

Each packet has a 16-byte protocol header followed by audio samples (24-bit stereo PCM, 3 bytes per sample).

Note: Downloaded audio is converted from 24-bit to 32-bit int32 for numpy compatibility.

### Upload Track

Request:
```
AA 55 07 00 89 [SLOT] [CHUNK_LO] [CHUNK_HI] [AUDIO_DATA...]
```

SLOT is the track slot (0-99). CHUNK_LO and CHUNK_HI form the chunk number (little-endian 16-bit). AUDIO_DATA is raw audio samples (24-bit stereo PCM, little-endian, 3 bytes per sample).

Audio must be split into chunks that fit within USB packet size limits (typically 1024 bytes). The device expects 24-bit audio, so 16-bit or 32-bit audio must be converted first.

Response (endpoint 0x81):
Acknowledgment, though it may be empty for some chunks.

### Delete Track

Request:
```
AA 55 03 00 88 [SLOT] 00 ...
```

or

```
AA 55 07 00 03 [SLOT] 00 ...
```

SLOT is the track slot (0-99).

Response (endpoint 0x81):
Acknowledgment.

### Play/Pause Track

Request:
```
AA 55 07 00 01 [SLOT] 00 ...
```

SLOT is the track slot (0-99). No response expected (fire and forget).

## Observations from Packet Captures

### GUI Connect (Frames 55-386)

Initial connection does USB enumeration and configuration, then queries the device identifier (response contains UTF-16 encoded device ID like "GL100174324669D7792E58") and firmware version (observed versions: "B1.0.0", "V1.4.2").

### Track Operations

Upload Track 0 (Frames 875-489658): Large multi-packet transfer with audio data chunked into ~1KB packets, each chunk acknowledged.

Download Track 1 (Frames 712975-824610): Request-response pattern where the host requests each chunk by number and the device responds with audio data until all data is transferred.

Delete Track (Frames 826815-826822): Short command-response exchange with confirmation from device.

Play/Pause (Frames 826815-826814): Single command packet, no response expected.

## Implementation Notes

Multi-packet Transfers: Large audio tracks need to be split into chunks. Track the chunk number to ensure proper reassembly.

Endianness: All multi-byte values (chunk numbers, sizes) are little-endian.

Padding: Command packets are typically padded to 64 bytes with zeros.

Timeouts: Short operations (delete, play) use 1 second timeout. Long operations (download, upload) use 5 second timeout.

Error Handling: The device may not always send acknowledgments. Lack of response doesn't necessarily indicate failure.

Audio Format: The GL100 works with 24-bit 44.1kHz stereo PCM internally. Downloaded audio is converted to 32-bit int32 for numpy compatibility. Audio files in other formats must be converted before upload.

