"""USB protocol implementation for Mooer GL100 looper pedal."""

import struct
from dataclasses import dataclass
from typing import List, Optional
import numpy as np

CRC_TABLE = [
    0x0000,
    0x1021,
    0x2042,
    0x3063,
    0x4084,
    0x50A5,
    0x60C6,
    0x70E7,
    0x8108,
    0x9129,
    0xA14A,
    0xB16B,
    0xC18C,
    0xD1AD,
    0xE1CE,
    0xF1EF,
    0x1231,
    0x0210,
    0x3273,
    0x2252,
    0x52B5,
    0x4294,
    0x72F7,
    0x62D6,
    0x9339,
    0x8318,
    0xB37B,
    0xA35A,
    0xD3BD,
    0xC39C,
    0xF3FF,
    0xE3DE,
    0x2462,
    0x3443,
    0x0420,
    0x1401,
    0x64E6,
    0x74C7,
    0x44A4,
    0x5485,
    0xA56A,
    0xB54B,
    0x8528,
    0x9509,
    0xE5EE,
    0xF5CF,
    0xC5AC,
    0xD58D,
    0x3653,
    0x2672,
    0x1611,
    0x0630,
    0x76D7,
    0x66F6,
    0x5695,
    0x46B4,
    0xB75B,
    0xA77A,
    0x9719,
    0x8738,
    0xF7DF,
    0xE7FE,
    0xD79D,
    0xC7BC,
    0x48C4,
    0x58E5,
    0x6886,
    0x78A7,
    0x0840,
    0x1861,
    0x2802,
    0x3823,
    0xC9CC,
    0xD9ED,
    0xE98E,
    0xF9AF,
    0x8948,
    0x9969,
    0xA90A,
    0xB92B,
    0x5AF5,
    0x4AD4,
    0x7AB7,
    0x6A96,
    0x1A71,
    0x0A50,
    0x3A33,
    0x2A12,
    0xDBFD,
    0xCBDC,
    0xFBBF,
    0xEB9E,
    0x9B79,
    0x8B58,
    0xBB3B,
    0xAB1A,
    0x6CA6,
    0x7C87,
    0x4CE4,
    0x5CC5,
    0x2C22,
    0x3C03,
    0x0C60,
    0x1C41,
    0xEDAE,
    0xFD8F,
    0xCDEC,
    0xDDCD,
    0xAD2A,
    0xBD0B,
    0x8D68,
    0x9D49,
    0x7E97,
    0x6EB6,
    0x5ED5,
    0x4EF4,
    0x3E13,
    0x2E32,
    0x1E51,
    0x0E70,
    0xFF9F,
    0xEFBE,
    0xDFDD,
    0xCFFC,
    0xBF1B,
    0xAF3A,
    0x9F59,
    0x8F78,
    0x9188,
    0x81A9,
    0xB1CA,
    0xA1EB,
    0xD10C,
    0xC12D,
    0xF14E,
    0xE16F,
    0x1080,
    0x00A1,
    0x30C2,
    0x20E3,
    0x5004,
    0x4025,
    0x7046,
    0x6067,
    0x83B9,
    0x9398,
    0xA3FB,
    0xB3DA,
    0xC33D,
    0xD31C,
    0xE37F,
    0xF35E,
    0x02B1,
    0x1290,
    0x22F3,
    0x32D2,
    0x4235,
    0x5214,
    0x6277,
    0x7256,
    0xB5EA,
    0xA5CB,
    0x95A8,
    0x8589,
    0xF56E,
    0xE54F,
    0xD52C,
    0xC50D,
    0x34E2,
    0x24C3,
    0x14A0,
    0x0481,
    0x7466,
    0x6447,
    0x5424,
    0x4405,
    0xA7DB,
    0xB7FA,
    0x8799,
    0x97B8,
    0xE75F,
    0xF77E,
    0xC71D,
    0xD73C,
    0x26D3,
    0x36F2,
    0x0691,
    0x16B0,
    0x6657,
    0x7676,
    0x4615,
    0x5634,
    0xD94C,
    0xC96D,
    0xF90E,
    0xE92F,
    0x99C8,
    0x89E9,
    0xB98A,
    0xA9AB,
    0x5844,
    0x4865,
    0x7806,
    0x6827,
    0x18C0,
    0x08E1,
    0x3882,
    0x28A3,
    0xCB7D,
    0xDB5C,
    0xEB3F,
    0xFB1E,
    0x8BF9,
    0x9BD8,
    0xABBB,
    0xBB9A,
    0x4A75,
    0x5A54,
    0x6A37,
    0x7A16,
    0x0AF1,
    0x1AD0,
    0x2AB3,
    0x3A92,
    0xFD2E,
    0xED0F,
    0xDD6C,
    0xCD4D,
    0xBDAA,
    0xAD8B,
    0x9DE8,
    0x8DC9,
    0x7C26,
    0x6C07,
    0x5C64,
    0x4C45,
    0x3CA2,
    0x2C83,
    0x1CE0,
    0x0CC1,
    0xEF1F,
    0xFF3E,
    0xCF5D,
    0xDF7C,
    0xAF9B,
    0xBFBA,
    0x8FD9,
    0x9FF8,
    0x6E17,
    0x7E36,
    0x4E55,
    0x5E74,
    0x2E93,
    0x3EB2,
    0x0ED1,
    0x1EF0,
]


def crc16(data: bytes) -> int:
    chk = 0
    for byte in data:
        chk = CRC_TABLE[(chk >> 8) ^ byte] ^ (chk << 8)
        chk &= 0xFFFF
    return (~chk) & 0xFFFF


# USB endpoints
EP_OUT = 0x02  # Host to device (commands)
EP_OUT_DATA = 0x03  # Host to device (data)
EP_IN_83 = 0x83  # Device to host (data)
EP_IN_81 = 0x81  # Device to host (status)

CMD_HEADER = bytes([0x3F, 0xAA, 0x55])
CMD_INIT_UPLOAD = 0x01
CMD_TRACK_OPS = 0x07
SUBCMD_DELETE = 0x03
SUBCMD_DOWNLOAD = 0x82
SUBCMD_UPLOAD = 0x84
SUBCMD_LIST = 0x88
SUBCMD_PLAY = 0x8A
SAMPLE_RATE = 44100
DEVICE_BYTES_PER_SAMPLE = 3
TRANSFER_BYTES_PER_SAMPLE = 2
CHANNELS = 2
DEVICE_SIZE_MULTIPLIER = 1.0


@dataclass
class TrackInfo:
    slot: int
    has_track: bool
    duration: float
    size: int


class GL100Protocol:
    MAX_TRACKS = 100
    MAX_PACKET_SIZE = 1024

    @staticmethod
    def create_delete_command(slot: int) -> bytes:
        """Create a delete track command.

        Args:
            slot: Track slot number (0-99)

        Returns:
            Command bytes to send to device
        """
        if not 0 <= slot < GL100Protocol.MAX_TRACKS:
            raise ValueError(f"Slot must be 0-{GL100Protocol.MAX_TRACKS-1}")

        # Command structure from capture: 3F AA 55 03 00 88 <slot_lo> <slot_hi> <crc_hi> <crc_lo> ...
        cmd = bytearray(64)
        cmd[0:3] = CMD_HEADER
        cmd[3] = 0x03  # Delete Type
        cmd[4] = 0x00
        cmd[5] = 0x88  # Delete Subcommand
        struct.pack_into("<H", cmd, 6, slot)  # Slot at offset 6

        # Calculate CRC-16 on bytes 3 through 7 (5 bytes)
        crc = crc16(cmd[3:8])
        cmd[8] = (crc >> 8) & 0xFF
        cmd[9] = crc & 0xFF

        return bytes(cmd)

    @staticmethod
    def create_download_command(slot: int, chunk: int = 0) -> bytes:
        if not 0 <= slot < GL100Protocol.MAX_TRACKS:
            raise ValueError(f"Slot must be 0-{GL100Protocol.MAX_TRACKS-1}")
        if not 0 <= chunk <= 65535:
            raise ValueError(f"Chunk must be 0-65535")

        cmd = bytearray(64)
        cmd[0:3] = CMD_HEADER
        cmd[3] = CMD_TRACK_OPS
        cmd[4] = 0x00
        cmd[5] = SUBCMD_DOWNLOAD
        cmd[6] = slot
        # Chunk index is 16-bit Little Endian at Offset 8. Offset 7 is padding.
        cmd[7] = 0x00
        struct.pack_into("<H", cmd, 8, chunk)

        # CRC Calculation
        crc = crc16(cmd[3:12])

        cmd[12] = (crc >> 8) & 0xFF  # CRC high byte (big-endian)
        cmd[13] = crc & 0xFF  # CRC low byte

        return bytes(cmd)

    @staticmethod
    def create_upload_command(slot: int, chunk: int, data: bytes) -> bytes:
        if not 0 <= slot < GL100Protocol.MAX_TRACKS:
            raise ValueError(f"Slot must be 0-{GL100Protocol.MAX_TRACKS-1}")
        if not 0 <= chunk <= 65535:
            raise ValueError(f"Chunk must be 0-65535")
        cmd = bytearray(64)
        cmd[0:3] = CMD_HEADER
        cmd[3] = CMD_TRACK_OPS
        cmd[4] = 0x00
        cmd[5] = SUBCMD_UPLOAD
        cmd[6] = slot
        # Chunk index is 16-bit Little Endian at Offset 8. Offset 7 is padding.
        cmd[7] = 0x00
        struct.pack_into("<H", cmd, 8, chunk)

        crc = crc16(cmd[3:12])
        cmd[12] = (crc >> 8) & 0xFF
        cmd[13] = crc & 0xFF
        return bytes(cmd)

    @staticmethod
    def create_query_track_command(slot: int) -> bytes:
        # Same as download chunk 0
        return GL100Protocol.create_download_command(slot, 0)

    @staticmethod
    def create_init_upload_command() -> bytes:
        cmd = bytearray(64)
        cmd[0:3] = CMD_HEADER
        cmd[3] = CMD_INIT_UPLOAD
        cmd[4] = 0x00
        cmd[5] = 0x86
        crc = crc16(cmd[3:6])
        cmd[6] = (crc >> 8) & 0xFF
        cmd[7] = crc & 0xFF
        return bytes(cmd)

    @staticmethod
    def create_play_command(slot: int) -> bytes:
        """Create a play/pause track command.

        Args:
            slot: Track slot number (0-99)

        Returns:
            Command bytes to send to device
        """
        if not 0 <= slot < GL100Protocol.MAX_TRACKS:
            raise ValueError(f"Slot must be 0-{GL100Protocol.MAX_TRACKS-1}")

        # Command structure from capture: 3F AA 55 07 00 8A 01 00 <slot_lo> <slot_hi> ...
        # Byte 6 = 0x01 means "play", may also support 0x00 for "pause"
        cmd = bytearray(64)
        cmd[0:3] = CMD_HEADER
        cmd[3] = CMD_TRACK_OPS
        cmd[4] = 0x00
        cmd[5] = SUBCMD_PLAY  # 0x8A
        cmd[6] = 0x01  # Play action (0x01 = play, 0x00 = pause?)
        cmd[7] = 0x00  # Padding
        struct.pack_into("<H", cmd, 8, slot)  # Slot at offset 8

        # Calculate CRC-16 on bytes 3..11
        crc = crc16(cmd[3:12])
        cmd[12] = (crc >> 8) & 0xFF
        cmd[13] = crc & 0xFF

        return bytes(cmd)

    @staticmethod
    def create_play_stream_command(slot: int, chunk: int = 0) -> bytes:
        """Create a play streaming command for real-time audio playback.

        Based on packet capture analysis, the device streams audio chunks when
        sent multiple play commands. This command includes a chunk parameter.

        Args:
            slot: Track slot number (0-99)
            chunk: Chunk/frame number for streaming (0-255)

        Returns:
            Command bytes to send to device
        """
        if not 0 <= slot < GL100Protocol.MAX_TRACKS:
            raise ValueError(f"Slot must be 0-{GL100Protocol.MAX_TRACKS-1}")
        if not 0 <= chunk <= 255:
            raise ValueError(f"Chunk must be 0-255")

        # Command structure: 3F AA 55 07 00 8A 01 00 <slot> <chunk> ...
        # Byte 8 = slot number
        # Byte 9 = chunk/frame number (based on packet capture analysis)
        cmd = bytearray(64)
        cmd[0:3] = CMD_HEADER
        cmd[3] = CMD_TRACK_OPS
        cmd[4] = 0x00
        cmd[5] = SUBCMD_PLAY  # 0x8A
        cmd[6] = 0x01  # Play action
        cmd[7] = 0x00  # Padding
        cmd[8] = slot  # Slot number
        cmd[9] = chunk  # Chunk/frame number

        # Calculate CRC-16 on bytes 3..11
        crc = crc16(cmd[3:12])
        cmd[12] = (crc >> 8) & 0xFF
        cmd[13] = crc & 0xFF

        return bytes(cmd)

    @staticmethod
    def parse_track_list_response(data: bytes) -> List[TrackInfo]:
        tracks = []
        offset = 16
        for slot in range(GL100Protocol.MAX_TRACKS):
            if offset + 8 > len(data):
                break
            has_track = data[offset] != 0
            device_reported_size = struct.unpack("<I", data[offset + 4 : offset + 8])[0]

            # Calculate duration based on 24-bit stereo size (6 bytes/frame)
            # duration = frames / sample_rate = (size / 6) / 44100
            duration = device_reported_size / (6 * SAMPLE_RATE)

            tracks.append(
                TrackInfo(
                    slot=slot,
                    has_track=has_track,
                    duration=duration,
                    size=device_reported_size,
                )
            )
            offset += 8
        return tracks

    @staticmethod
    def parse_track_info_header(data: bytes) -> tuple[bool, int]:
        if len(data) < 12:
            raise ValueError(f"Data too short for track info header: {len(data)} bytes")
        track_exists = data[0] == 0x01
        track_size = struct.unpack("<I", data[4:8])[0]
        return track_exists, track_size

    @staticmethod
    def parse_audio_data(data: bytes, skip_header: bool = True) -> np.ndarray:
        audio_offset = 18 if skip_header else 0
        audio_bytes = data[audio_offset:]
        num_frames = len(audio_bytes) // 6
        trimmed_bytes = audio_bytes[: num_frames * 6]
        if len(trimmed_bytes) == 0:
            return np.array([], dtype=np.int32).reshape(0, 2)
        num_samples = num_frames * 2
        byte_array = np.frombuffer(trimmed_bytes, dtype=np.uint8).reshape(num_samples, 3)
        samples = (
            byte_array[:, 0].astype(np.int32)
            | (byte_array[:, 1].astype(np.int32) << 8)
            | (byte_array[:, 2].astype(np.int32) << 16)
        )
        samples = (samples << 8) >> 8
        samples = samples << 8
        samples = samples.reshape(num_frames, 2)
        return samples

    @staticmethod
    def encode_audio_data(audio: np.ndarray) -> bytes:
        """Encode numpy audio array to 24-bit device format.

        Args:
            audio: Numpy array of audio samples (int16 or int32)

        Returns:
            Raw bytes in 24-bit format (3 bytes per sample, little-endian)
        """
        # Convert to int32 first if int16
        if audio.dtype == np.int16:
            audio = audio.astype(np.int32) << 8
        
        # Handle Mono to Stereo with -3dB attenuation
        if len(audio.shape) == 1 or (len(audio.shape) == 2 and audio.shape[1] == 1):
            # Flatten if 2D mono
            if len(audio.shape) == 2:
                audio = audio.flatten()
            
            # Convert to float for scaling
            audio_float = audio.astype(np.float64)
            
            # Apply -3dB attenuation (0.7071)
            audio_float *= 0.70710678
            
            # Convert back to int32
            audio = audio_float.astype(np.int32)
            
            # Duplicate to stereo
            audio = np.stack([audio, audio], axis=1)

        # Ensure correct range for int32
        if audio.dtype != np.int32:
            audio = np.clip(audio, -2147483648, 2147483647).astype(np.int32)

        # Scale from int32 to 24-bit range (divide by 256)
        audio_24bit = audio >> 8

        # Encode to 24-bit little-endian bytes
        # Each sample: 3 bytes [LSB, mid, MSB]
        output = bytearray()
        for frame in audio_24bit:
            for sample in frame:
                # Handle negative numbers with two's complement
                if sample < 0:
                    sample = (1 << 24) + sample
                # Pack as 24-bit little-endian
                output.extend([sample & 0xFF, (sample >> 8) & 0xFF, (sample >> 16) & 0xFF])

        return bytes(output)
