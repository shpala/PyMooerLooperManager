# GL100 Upload/Download Protocol Analysis

This is an analysis of gl100-small.pcapng showing how the GL100 actually handles audio upload and download over USB.

The test case uploads out24bit.wav to slot 4 (frames 25-2112), then downloads it back as GL_LOOPFILE_04.wav (frames 2113-3188). The track is 264,600 bytes transferred in 260 chunks of 1024 bytes each.

## USB Endpoints

The device uses four endpoints:
- 0x02 (OUT): Commands from host (64 bytes)
- 0x03 (OUT): Audio data from host (1024 bytes per chunk)
- 0x81 (IN): Status and acknowledgments (64 bytes)
- 0x83 (IN): Audio data and track info to host (1024 bytes per chunk)

## CRC Calculation

CRC-16 is calculated on everything after the `3F AA 55` header and stored in big-endian format. It's the same CRC-16 algorithm used by the official MooerManager software.

## Command Structure

All commands start with `3F AA 55 <cmd_type> ...`

## Upload Protocol

### 1. Initial Command (Frame 25)
```
3F AA 55 01 00 86 39 81 00 00 00 00 ...
         ^^    ^^ ^^^^^ ^^
         |     |    |    |
         |     |    |    +-- CRC byte 2
         |     |    +------- CRC byte 1 (big-endian)
         |     +------------ Parameter (0x86)
         +------------------ Command type 0x01
```

Structure: `3F AA 55 01 00 <param> <CRC_H> <CRC_L> [padding]`

Command type 0x01 appears to initialize the upload. Parameter is 0x86 (purpose unclear). CRC is calculated on `01 00 86` and stored big-endian. The device responds with device info on endpoint 0x81.

### 2. Upload Data Chunks (Frames 29, 37, 45, ...)

Each chunk requires sending a command followed by the actual data.

Command (endpoint 0x02):
```
3F AA 55 07 00 84 04 00 XX 00 00 00 YY YY 00 00 ...
         ^^    ^^ ^^    ^^          ^^^^^
         |     |  |     |             |
         |     |  |     |             +-- CRC (big-endian)
         |     |  |     +---------------- Chunk number (8-bit)
         |     |  +---------------------- Slot number
         |     +------------------------- Subcommand 0x84 (upload chunk)
         +------------------------------- Command type 0x07
```

Structure: `3F AA 55 07 00 84 <slot> 00 <chunk> 00 00 00 <CRC_H> <CRC_L> [padding]`

Command type 0x07 is for track operations. Subcommand 0x84 uploads a data chunk. The slot is 0x04 for slot 4. Chunk number is an 8-bit value at offset 7 starting from 0x00. Bytes 8-11 are always `00 00 00` (probably reserved). CRC is calculated on everything after the header.

Data (endpoint 0x03):
Each chunk is 1024 bytes of audio data. The first chunk includes a 12-byte header: `01 00 01 00 <size_32le> 00 00 00 00 <audio_data>` where byte 0 is `01` (track exists), bytes 4-7 contain the track size in little-endian, and audio data starts at byte 12.

### 3. Finalize Upload (Frame 2109)
```
3F AA 55 07 00 82 04 00 00 00 00 00 83 EF 00 00 ...
         ^^    ^^ ^^    ^^          ^^^^^
         |     |  |     |             |
         |     |  |     |             +-- CRC (big-endian)
         |     |  |     +---------------- Chunk 0x00
         |     |  +---------------------- Slot number
         |     +------------------------- Subcommand 0x82 (finalize/query)
         +------------------------------- Command type 0x07
```

Structure: `3F AA 55 07 00 82 <slot> 00 00 00 00 00 <CRC_H> <CRC_L> [padding]`

Subcommand 0x82 finalizes the upload and queries the track. The device responds on endpoint 0x83 with track info in the same 12-byte header format.

## Download Protocol

Download uses the same subcommand 0x82, just with incrementing chunk numbers to request each chunk.

### Download Data Chunks (Frames 2113, 2117, 2121, ...)

Command (endpoint 0x02):
```
3F AA 55 07 00 82 04 00 XX 00 00 00 YY YY 00 00 ...
         ^^    ^^ ^^    ^^          ^^^^^
         |     |  |     |             |
         |     |  |     |             +-- CRC (big-endian)
         |     |  |     +---------------- Chunk number (8-bit)
         |     |  +---------------------- Slot number
         |     +------------------------- Subcommand 0x82 (download/query)
         +------------------------------- Command type 0x07
```

Structure: `3F AA 55 07 00 82 <slot> 00 <chunk> 00 00 00 <CRC_H> <CRC_L> [padding]`

Same format as upload finalize. Chunk number is 8-bit and increments: 0x00, 0x01, 0x02, etc.

Response (endpoint 0x83):
The device sends 1024 bytes per chunk. First chunk includes the 12-byte header (same as upload). Subsequent chunks are raw audio data.

## Audio Data Format

The 264,600 byte test track works out to exactly 1 second of audio:
- 44,100 Hz sample rate
- 24-bit (3 bytes per sample)
- 2 channels (stereo)
- Little-endian PCM

264,600 bytes ÷ 3 bytes/sample ÷ 2 channels = 44,100 samples = 1 second @ 44.1kHz

## Track Info Header (12 bytes)

This header appears in responses on endpoint 0x83:
```
Offset  Size  Description
0       1     Track exists (0x01 = exists, 0x00 = empty)
1       1     Unknown
2       1     Unknown
3       1     Unknown
4       4     Track size in bytes (little-endian 32-bit)
8       4     Unknown (padding or metadata)
12+     N     Audio data
```

Example: `01 00 01 00 98 09 04 00 00 00 00 00`
- Byte 0 is 0x01 (track exists)
- Bytes 4-7 are 0x00040998 = 264,600 bytes

