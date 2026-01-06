"""Tests for GL100 protocol implementation."""

import pytest
import numpy as np
from gl100.protocol import GL100Protocol, TrackInfo


class TestProtocol:
    """Test protocol command generation."""

    def test_delete_command(self):
        """Test delete command generation."""
        cmd = GL100Protocol.create_delete_command(0)
        assert cmd[0:3] == bytes([0x3F, 0xAA, 0x55])
        assert cmd[3] == 0x03  # Delete command
        assert cmd[5] == 0x88  # Delete Subcommand
        assert cmd[6] == 0  # Slot 0 LSB
        assert cmd[7] == 0  # Slot 0 MSB

        cmd = GL100Protocol.create_delete_command(99)
        assert cmd[6] == 99  # Slot 99 LSB
        assert cmd[7] == 0  # Slot 99 MSB

        # Test CRC is present at 8, 9
        assert cmd[8] != 0 or cmd[9] != 0

    def test_delete_command_invalid_slot(self):
        """Test delete command with invalid slot."""
        with pytest.raises(ValueError):
            GL100Protocol.create_delete_command(-1)

        with pytest.raises(ValueError):
            GL100Protocol.create_delete_command(100)

    def test_download_command(self):
        """Test download command generation."""
        cmd = GL100Protocol.create_download_command(5, chunk=0)
        assert cmd[0:3] == bytes([0x3F, 0xAA, 0x55])
        assert cmd[3] == 0x07  # Track ops
        assert cmd[5] == 0x82  # Download
        assert cmd[6] == 5  # Slot 5
        assert cmd[7] == 0  # Padding
        assert cmd[8] == 0  # Chunk number (LSB)

        # Test with max chunk number (byte 8 check)
        cmd = GL100Protocol.create_download_command(10, chunk=255)
        assert cmd[7] == 0
        assert cmd[8] == 255  # Chunk number LSB
        assert cmd[9] == 0  # Chunk number MSB

        # Test with chunk > 255 (e.g. 256 -> 0x0100)
        cmd = GL100Protocol.create_download_command(10, chunk=256)
        assert cmd[7] == 0
        assert cmd[8] == 0  # LSB
        assert cmd[9] == 1  # MSB

        # Test CRC is calculated
        assert cmd[12] != 0 or cmd[13] != 0  # CRC should be present

    def test_upload_command(self):
        """Test upload command generation."""
        data = bytes([1, 2, 3, 4])
        cmd = GL100Protocol.create_upload_command(3, chunk=0, data=data)
        assert cmd[0:3] == bytes([0x3F, 0xAA, 0x55])
        assert cmd[3] == 0x07  # Track ops
        assert cmd[5] == 0x84  # Upload subcommand
        assert cmd[6] == 3  # Slot 3
        assert cmd[7] == 0  # Padding
        assert cmd[8] == 0  # Chunk number LSB

        # Test CRC is calculated
        assert cmd[12] != 0 or cmd[13] != 0  # CRC should be present

        # Test with chunk 255
        cmd = GL100Protocol.create_upload_command(3, chunk=255, data=data)
        assert cmd[7] == 0
        assert cmd[8] == 255

    def test_query_track_command(self):
        """Test query track command generation."""
        cmd = GL100Protocol.create_query_track_command(5)
        assert cmd[0:3] == bytes([0x3F, 0xAA, 0x55])
        assert cmd[3] == 0x07  # Track ops
        assert cmd[5] == 0x82  # Query
        assert cmd[6] == 5  # Slot 5

    def test_play_command(self):
        """Test play command generation."""
        cmd = GL100Protocol.create_play_command(0)
        assert cmd[0:3] == bytes([0x3F, 0xAA, 0x55])
        assert cmd[3] == 0x07  # Track ops
        assert cmd[5] == 0x8A  # Play subcommand
        assert cmd[6] == 0x01  # Play action (0x01 = play)
        assert cmd[8] == 0  # Slot 0 LSB
        assert cmd[9] == 0  # Slot 0 MSB

        cmd = GL100Protocol.create_play_command(99)
        assert cmd[8] == 99  # Slot 99 LSB
        assert cmd[9] == 0  # Slot 99 MSB

    def test_play_stream_command(self):
        """Test play streaming command generation."""
        cmd = GL100Protocol.create_play_stream_command(1, chunk=0)
        assert cmd[0:3] == bytes([0x3F, 0xAA, 0x55])
        assert cmd[3] == 0x07  # Track ops
        assert cmd[5] == 0x8A  # Play subcommand
        assert cmd[6] == 0x01  # Play action
        assert cmd[7] == 0x00  # Padding
        assert cmd[8] == 1  # Slot 1
        assert cmd[9] == 0  # Chunk 0

        # Test with different chunk numbers
        cmd = GL100Protocol.create_play_stream_command(5, chunk=10)
        assert cmd[8] == 5  # Slot 5
        assert cmd[9] == 10  # Chunk 10

        cmd = GL100Protocol.create_play_stream_command(99, chunk=255)
        assert cmd[8] == 99  # Slot 99
        assert cmd[9] == 255  # Chunk 255

        # Test CRC is calculated
        assert cmd[12] != 0 or cmd[13] != 0

    def test_audio_encoding(self):
        """Test audio data encoding to 24-bit format."""
        # Test stereo audio (int32 format)
        audio = np.array([[100 << 8, -100 << 8], [200 << 8, -200 << 8]], dtype=np.int32)
        encoded = GL100Protocol.encode_audio_data(audio)
        # 2 frames * 2 channels * 3 bytes = 12 bytes
        assert len(encoded) == 12

        # Test mono to stereo conversion (int16 format)
        mono = np.array([100, 200], dtype=np.int16)
        encoded = GL100Protocol.encode_audio_data(mono)
        # 2 frames * 2 channels * 3 bytes = 12 bytes
        assert len(encoded) == 12

        # Test round-trip: encode then decode should match
        original = np.array([[1000 << 8, -1000 << 8], [2000 << 8, -2000 << 8]], dtype=np.int32)
        encoded = GL100Protocol.encode_audio_data(original)
        decoded = GL100Protocol.parse_audio_data(encoded, skip_header=False)
        assert np.array_equal(decoded, original)

    def test_init_upload_command(self):
        """Test initial upload command generation."""
        cmd = GL100Protocol.create_init_upload_command()
        assert cmd[0:3] == bytes([0x3F, 0xAA, 0x55])
        assert cmd[3] == 0x01  # Init upload command
        assert cmd[4] == 0x00
        assert cmd[5] == 0x86  # Parameter
        # Test CRC is calculated
        assert cmd[6] != 0 or cmd[7] != 0  # CRC should be present

    def test_track_info_header_parsing(self):
        """Test track info header parsing."""
        # Create a track info header: exists=1, size=264600 bytes
        header = bytearray(12)
        header[0] = 0x01  # Track exists
        header[4:8] = (264600).to_bytes(4, byteorder="little")  # Track size

        exists, size = GL100Protocol.parse_track_info_header(bytes(header))
        assert exists is True
        assert size == 264600

        # Test empty track
        header[0] = 0x00
        exists, size = GL100Protocol.parse_track_info_header(bytes(header))
        assert exists is False

    def test_audio_parsing(self):
        """Test audio data parsing (24-bit to int32)."""
        # 18-byte header (first download chunk only)
        header = bytes(18)

        # Create 24-bit audio samples (little-endian)
        # Sample 1 (L): 100 = 0x000064
        # Sample 1 (R): -100 = 0xFFFF9C (24-bit two's complement)
        # Sample 2 (L): 1000 = 0x0003E8
        # Sample 2 (R): -1000 = 0xFFFC18
        audio_data = bytearray()
        # L1: 100
        audio_data.extend([0x64, 0x00, 0x00])
        # R1: -100 (0xFFFF9C in 24-bit)
        audio_data.extend([0x9C, 0xFF, 0xFF])
        # L2: 1000
        audio_data.extend([0xE8, 0x03, 0x00])
        # R2: -1000 (0xFFFC18 in 24-bit)
        audio_data.extend([0x18, 0xFC, 0xFF])

        response = header + bytes(audio_data)

        parsed = GL100Protocol.parse_audio_data(response, skip_header=True)
        assert parsed.shape == (2, 2), f"Expected shape (2, 2), got {parsed.shape}"
        assert parsed.dtype == np.int32, f"Expected int32, got {parsed.dtype}"
        # Values are scaled to 32-bit range by left-shifting 8 bits (multiply by 256)
        assert parsed[0, 0] == 100 << 8, f"Expected {100 << 8}, got {parsed[0, 0]}"
        assert parsed[0, 1] == -100 << 8, f"Expected {-100 << 8}, got {parsed[0, 1]}"
        assert parsed[1, 0] == 1000 << 8, f"Expected {1000 << 8}, got {parsed[1, 0]}"
        assert parsed[1, 1] == -1000 << 8, f"Expected {-1000 << 8}, got {parsed[1, 1]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
