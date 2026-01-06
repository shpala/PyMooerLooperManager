"""Low-level USB communication with the GL100 device.

This module handles USB device discovery, connection, and raw data transfer.
"""

import usb.core
import usb.util
from typing import Optional, List, Callable
import logging
import struct
import time
import threading

from gl100.protocol import (
    GL100Protocol,
    TrackInfo,
    SAMPLE_RATE,
    TRANSFER_BYTES_PER_SAMPLE,
    DEVICE_SIZE_MULTIPLIER,
    CHANNELS,
    EP_OUT_DATA,
)
import numpy as np

try:
    import pyaudio

    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None


logger = logging.getLogger(__name__)


class GL100Device:
    """USB interface for Mooer GL100 looper pedal."""

    # USB IDs for Mooer GL100 (from lsusb: Bus 001 Device 006: ID 34db:0008 Mooer Corporation GL100)
    VENDOR_ID = 0x34DB  # Mooer Corporation
    PRODUCT_ID = 0x0008  # GL100

    # USB endpoints
    EP_OUT = 0x02
    EP_IN_DATA = 0x83
    EP_IN_STATUS = 0x81

    # Timeouts in milliseconds
    TIMEOUT_SHORT = 5000
    TIMEOUT_LONG = 5000

    def __init__(self) -> None:
        """Initialize GL100 device interface."""
        self.dev: Optional[usb.core.Device] = None
        self.protocol = GL100Protocol()
        self._connected = False
        self._stop_playback = threading.Event()
        self._playback_thread: Optional[threading.Thread] = None

    def connect(self) -> bool:
        """Connect to the GL100 device.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Find the device
            self.dev = usb.core.find(idVendor=self.VENDOR_ID, idProduct=self.PRODUCT_ID)

            if self.dev is None:
                logger.error("GL100 device not found")
                return False

            # Detach kernel driver from all interfaces if necessary
            # The GL100 has 2 interfaces, both may have kernel drivers attached
            for interface in [0, 1]:
                try:
                    if self.dev.is_kernel_driver_active(interface):
                        self.dev.detach_kernel_driver(interface)
                        logger.debug(f"Detached kernel driver from interface {interface}")
                except usb.core.USBError as e:
                    logger.warning(
                        f"Could not detach kernel driver from interface {interface}: {e}"
                    )
                except Exception as e:
                    # Interface might not exist, that's okay
                    logger.debug(f"Interface {interface} check failed: {e}")

            # Set configuration
            self.dev.set_configuration()

            # Claim the interfaces we need
            # Interface 0: has endpoints 0x81 (IN), 0x02 (OUT)
            # Interface 1: has endpoints 0x83 (IN), 0x03 (OUT)
            try:
                usb.util.claim_interface(self.dev, 0)
                usb.util.claim_interface(self.dev, 1)
                logger.debug("Claimed interfaces 0 and 1")
            except Exception as e:
                logger.warning(f"Could not claim interfaces: {e}")

            self._connected = True

            logger.info("Connected to GL100 device")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to GL100: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from the GL100 device."""
        if self.dev is not None:
            try:
                # Reattach kernel driver to be polite
                for interface in [0, 1]:
                    try:
                        self.dev.attach_kernel_driver(interface)
                        logger.debug(f"Reattached kernel driver to interface {interface}")
                    except Exception:
                        pass  # Might not have been detached or interface doesn't exist

                usb.util.dispose_resources(self.dev)
                self._connected = False
                logger.info("Disconnected from GL100 device")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")

    def is_connected(self) -> bool:
        """Check if device is connected.

        Returns:
            True if connected, False otherwise
        """
        return self._connected and self.dev is not None

    def _write(self, data: bytes, endpoint: int = None, timeout: int = TIMEOUT_SHORT) -> int:
        """Write data to the device using interrupt transfer.

        Args:
            data: Bytes to write
            endpoint: USB endpoint (defaults to EP_OUT)
            timeout: Timeout in milliseconds

        Returns:
            Number of bytes written
        """
        if not self.is_connected():
            raise RuntimeError("Device not connected")

        if endpoint is None:
            endpoint = self.EP_OUT

        # GL100 uses interrupt transfers (URB type 0x01)
        # PyUSB's write() method uses the correct transfer type based on endpoint
        written = self.dev.write(endpoint, data, timeout)
        return written

    def _read(self, size: int = 1024, endpoint: int = None, timeout: int = TIMEOUT_SHORT) -> bytes:
        """Read data from the device using interrupt transfer.

        Args:
            size: Maximum bytes to read
            endpoint: USB endpoint to read from (defaults to EP_IN_DATA)
            timeout: Timeout in milliseconds

        Returns:
            Bytes read from device
        """
        if not self.is_connected():
            raise RuntimeError("Device not connected")

        if endpoint is None:
            endpoint = self.EP_IN_DATA

        # GL100 uses interrupt transfers (URB type 0x01)
        # PyUSB automatically uses the correct transfer type based on endpoint
        data = self.dev.read(endpoint, size, timeout)
        return bytes(data)

    def list_tracks(self) -> List[TrackInfo]:
        """Get list of all tracks on the device.

        The GL100 doesn't have a "list all" command, so we query each slot individually.

        Returns:
            List of TrackInfo objects for all 100 slots
        """
        tracks = []

        for slot in range(GL100Protocol.MAX_TRACKS):
            try:
                # Query this slot
                cmd = self.protocol.create_query_track_command(slot)
                self._write(cmd)

                # Read response on endpoint 0x83
                response = self._read(size=1024, endpoint=0x83, timeout=self.TIMEOUT_SHORT)

                # Parse track info from response
                # Response format (from device testing):
                # Byte 0: status byte (usually 0x01 if track exists, 0x00 if empty)
                # Bytes 4-7: Track size in bytes (little-endian 32-bit)

                # Log first 8 bytes for debugging slot 0 issue
                if len(response) >= 8:
                    logger.debug(
                        f"Slot {slot} response: byte[0]={response[0]:#04x}, "
                        f"bytes[0-7]={response[:8].hex()}"
                    )

                has_track = response[0] != 0x00 if len(response) > 0 else False

                # Parse track size from bytes 4-7 (little-endian)
                if has_track and len(response) >= 8:
                    device_reported_size = struct.unpack("<I", response[4:8])[0]
                    # Apply the 1.4x conversion factor (see protocol.py for explanation)
                    actual_size = int(device_reported_size * DEVICE_SIZE_MULTIPLIER)
                    # Calculate duration based on actual 16-bit stereo size
                    duration = actual_size / (SAMPLE_RATE * TRANSFER_BYTES_PER_SAMPLE * CHANNELS)
                    size = actual_size
                else:
                    size = 0
                    duration = 0.0

                track_info = TrackInfo(slot=slot, has_track=has_track, duration=duration, size=size)
                tracks.append(track_info)

                logger.debug(f"Slot {slot}: {'has track' if has_track else 'empty'}")

            except Exception as e:
                logger.warning(f"Failed to query slot {slot}: {e}")
                # Add empty slot on error
                tracks.append(TrackInfo(slot=slot, has_track=False, duration=0.0, size=0))

        return tracks

    def download_track(
        self, slot: int, progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> np.ndarray:
        """Download audio track from device.

        Args:
            slot: Track slot number (0-99)
            progress_callback: Optional callback function(bytes_downloaded, total_bytes)

        Returns:
            Numpy array of audio samples

        Raises:
            ValueError: If slot is invalid
            RuntimeError: If download fails
        """
        logger.info(f"Downloading track from slot {slot}")

        # Request first chunk using query command (same as list_tracks does)
        # This returns 18-byte header + first chunk of audio data
        cmd = self.protocol.create_query_track_command(slot)
        self._write(cmd)

        # Read first chunk response
        first_chunk = self._read(size=1024, endpoint=0x83, timeout=self.TIMEOUT_SHORT)

        if len(first_chunk) < 18:
            raise RuntimeError(f"First chunk too small: {len(first_chunk)} bytes")

        # Parse header from first chunk to get track info
        track_exists, track_size = self.protocol.parse_track_info_header(first_chunk)

        if not track_exists:
            raise RuntimeError(f"No track in slot {slot}")

        logger.info(f"Track size: {track_size:,} bytes ({track_size/(1024**2):.2f} MB)")

        # Chunk 0 contains metadata but we ignore its audio payload because
        # Chunk 1 returns the audio starting from Frame 0.
        raw_data = bytearray()

        chunk_size = 1024
        num_chunks = (track_size + chunk_size - 1) // chunk_size

        # Download chunks starting from 1
        for chunk_idx in range(1, num_chunks + 1):

            # Request next chunk
            cmd = self.protocol.create_download_command(slot, chunk=chunk_idx)
            self._write(cmd)

            try:
                # Read chunk data
                data = self._read(size=1024, endpoint=0x83, timeout=self.TIMEOUT_SHORT)

                if len(data) == 0:
                    break

                raw_data.extend(data)

                # Update progress (batch every 10 chunks to reduce GUI overhead)
                if progress_callback and chunk_idx % 10 == 0:
                    progress_callback(len(raw_data), track_size)

            except usb.core.USBError as e:
                logger.warning(f"USB error at chunk {chunk_idx}: {e}")
                break

        # Final progress update
        if progress_callback:
            progress_callback(len(raw_data), track_size)

        if len(raw_data) == 0:
            raise RuntimeError(f"No data received for slot {slot}")

        # Parse collected audio data
        # No header skipping because we started from Chunk 1 (Pure Audio)
        full_audio = self.protocol.parse_audio_data(raw_data, skip_header=False)

        # Trim to expected size
        total_frames = track_size // 6
        if len(full_audio) > total_frames:
            full_audio = full_audio[:total_frames]

        logger.info(
            f"Downloaded track from slot {slot}: "
            f"{len(full_audio)} samples, "
            f"{full_audio.nbytes:,} bytes ({full_audio.nbytes / (1024**2):.2f} MB)"
        )

        return full_audio

    def upload_track(
        self,
        slot: int,
        audio_data: np.ndarray,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> None:
        """Upload audio track to device.

        Args:
            slot: Track slot number (0-99)
            audio_data: Numpy array of audio samples
            progress_callback: Optional callback function(bytes_uploaded, total_bytes)

        Raises:
            ValueError: If slot is invalid
            RuntimeError: If upload fails
        """
        logger.info(f"Uploading track to slot {slot}")

        # 1. Send initial upload command
        init_cmd = self.protocol.create_init_upload_command()
        self._write(init_cmd, timeout=self.TIMEOUT_SHORT)
        try:
            self._read(size=64, endpoint=self.EP_IN_STATUS, timeout=self.TIMEOUT_SHORT)
        except usb.core.USBError:
            pass

        time.sleep(1)  # Give device time to prepare

        # Encode audio data to 24-bit format
        audio_bytes = self.protocol.encode_audio_data(audio_data)
        size_bytes = len(audio_bytes)

        # 2. Prepare chunks
        # Chunk 0: Size Header (4 bytes size + 1020 bytes padding)
        # Chunk 1+: Audio Data

        metadata_chunk = bytearray(1024)
        struct.pack_into("<I", metadata_chunk, 0, size_bytes)  # Size at offset 0

        chunk_size = 1024
        audio_chunks = [
            audio_bytes[i : i + chunk_size] for i in range(0, len(audio_bytes), chunk_size)
        ]

        all_data_chunks = [bytes(metadata_chunk)] + [
            bytes(c).ljust(chunk_size, b"\x00") for c in audio_chunks
        ]
        num_chunks = len(all_data_chunks)

        # 3. Upload all chunks
        for chunk_idx, chunk_data in enumerate(all_data_chunks):
            if chunk_idx > 65535:
                raise RuntimeError("Too many chunks")

            # Send upload chunk command (0x84)
            # Fixed in protocol.py: chunk index at byte 8
            cmd = self.protocol.create_upload_command(slot, chunk_idx, chunk_data)
            self._write(cmd, timeout=self.TIMEOUT_SHORT)

            # Read command acknowledgment on 0x81
            try:
                self._read(size=64, endpoint=self.EP_IN_STATUS, timeout=self.TIMEOUT_SHORT)
            except usb.core.USBError:
                pass

            # Send data chunk (1024 bytes on endpoint 0x03)
            try:
                self._write(chunk_data, endpoint=EP_OUT_DATA, timeout=self.TIMEOUT_SHORT)
            except usb.core.USBError as e:
                raise RuntimeError(f"Failed to write data chunk {chunk_idx}: {e}")

            # Read data acknowledgment on 0x81
            try:
                self._read(size=64, endpoint=self.EP_IN_STATUS, timeout=self.TIMEOUT_SHORT)
            except usb.core.USBError:
                pass

            # Update progress (batch every 10 chunks to reduce GUI overhead)
            if progress_callback and chunk_idx % 10 == 0:
                progress_callback(chunk_idx * chunk_size, len(audio_bytes))

        # Final progress update
        if progress_callback:
            total_bytes = num_chunks * chunk_size
            progress_callback(total_bytes, total_bytes)

        # 5. Finalize/verify upload with query command
        time.sleep(1)  # Give device a moment to commit
        finalize_cmd = self.protocol.create_query_track_command(slot)
        self._write(finalize_cmd, timeout=self.TIMEOUT_SHORT)

        # Read track info response on 0x83
        try:
            response = self._read(size=1024, endpoint=0x83, timeout=self.TIMEOUT_SHORT)
            if len(response) >= 12:
                exists, size = self.protocol.parse_track_info_header(response)
                logger.info(f"Upload verified: exists={exists}, size={size} bytes")
                if not exists:
                    logger.warning("Device reports track does not exist after upload!")
        except usb.core.USBError as e:
            logger.warning(f"Could not verify upload: {e}")

        logger.info(f"Uploaded {num_chunks} chunks to slot {slot}")

    def delete_track(self, slot: int) -> None:
        """Delete track from device.

        Args:
            slot: Track slot number (0-99)

        Raises:
            ValueError: If slot is invalid
            RuntimeError: If delete fails
        """
        logger.info(f"Deleting track from slot {slot}")

        cmd = self.protocol.create_delete_command(slot)
        self._write(cmd)

        # Read acknowledgment
        try:
            response = self._read(size=64, endpoint=self.EP_IN_STATUS)
            logger.info(f"Deleted track from slot {slot}")
        except usb.core.USBError as e:
            raise RuntimeError(f"Failed to delete track: {e}")

    def play_track(self, slot: int) -> None:
        """Play/pause track on device.

        Args:
            slot: Track slot number (0-99)

        Raises:
            ValueError: If slot is invalid
        """
        logger.info(f"Playing track from slot {slot}")

        cmd = self.protocol.create_play_command(slot)
        self._write(cmd)

        # Read response on endpoint 0x83 (based on packet capture)
        try:
            response = self._read(size=1024, endpoint=0x83, timeout=self.TIMEOUT_SHORT)
            logger.debug(f"Play response: {len(response)} bytes received")
        except usb.core.USBError as e:
            logger.warning(f"No response on endpoint 0x83: {e}")

    def play_track_streaming(
        self, slot: int, progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """Stream and play audio from device in real-time.

        This uses the download protocol to stream audio chunks and plays them
        through the computer's speakers using PyAudio.

        Args:
            slot: Track slot number (0-99)
            progress_callback: Optional callback function(chunks_played, total_chunks)

        Raises:
            ValueError: If slot is invalid
            RuntimeError: If PyAudio is not available or playback fails
        """
        if not PYAUDIO_AVAILABLE:
            raise RuntimeError("PyAudio is not installed. Install it with: pip install PyAudio")

        logger.info(f"Starting streaming playback from slot {slot}")

        # Get track info using download chunk 0
        try:
            cmd = self.protocol.create_query_track_command(slot)
            self._write(cmd)
            first_chunk = self._read(size=1024, endpoint=0x83, timeout=self.TIMEOUT_SHORT)

            if len(first_chunk) < 18:
                raise RuntimeError(f"Invalid first chunk response: {len(first_chunk)} bytes")

            track_exists, track_size = self.protocol.parse_track_info_header(first_chunk)

            if not track_exists:
                raise RuntimeError(f"No track in slot {slot}")

            logger.info(f"Track size: {track_size:,} bytes")

        except Exception as e:
            raise RuntimeError(f"Failed to get track info: {e}")

        # Calculate total chunks needed
        chunk_size = 1024
        total_chunks = (track_size + chunk_size - 1) // chunk_size

        # Initialize PyAudio
        p = pyaudio.PyAudio()

        try:
            # Open audio stream: 32-bit (same as downloaded WAV files)
            stream = p.open(
                format=pyaudio.paInt32,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                output=True,
                frames_per_buffer=1024,
            )

            self._stop_playback.clear()
            chunk_idx = 0

            # Buffer for leftover bytes from previous chunk (since 1024 % 6 != 0)
            remainder_buffer = bytearray()

            # Stream audio chunks using download command (chunks 1+)
            for chunk_idx in range(1, total_chunks + 1):
                if self._stop_playback.is_set():
                    logger.info("Playback stopped by user")
                    break

                try:
                    # Use download command to get next chunk
                    cmd = self.protocol.create_download_command(slot, chunk=chunk_idx)
                    self._write(cmd)

                    # Read audio data response
                    audio_data = self._read(size=1024, endpoint=0x83, timeout=self.TIMEOUT_SHORT)

                    if len(audio_data) == 0:
                        logger.warning(f"No data received for chunk {chunk_idx}")
                        break

                    # Add new data to buffer
                    remainder_buffer.extend(audio_data)

                    # Calculate how many full frames we have (6 bytes per frame)
                    num_frames = len(remainder_buffer) // 6
                    num_bytes_to_process = num_frames * 6

                    if num_bytes_to_process == 0:
                        continue

                    # Extract bytes to process
                    bytes_to_process = remainder_buffer[:num_bytes_to_process]
                    # Keep remainder for next chunk
                    remainder_buffer = remainder_buffer[num_bytes_to_process:]

                    # Parse audio data (no header for chunks >= 1)
                    audio_samples = self.protocol.parse_audio_data(bytes_to_process, skip_header=False)

                    if len(audio_samples) == 0:
                        continue

                    # Play as 32-bit audio (same format as downloaded WAV files)
                    stream.write(audio_samples.tobytes())

                    # Update progress
                    if progress_callback and chunk_idx % 10 == 0:
                        progress_callback(chunk_idx, total_chunks)

                except usb.core.USBError as e:
                    logger.warning(f"USB error at chunk {chunk_idx}: {e}")
                    break
                except Exception as e:
                    logger.error(f"Error playing chunk {chunk_idx}: {e}")
                    break

            # Final progress update
            if progress_callback:
                progress_callback(chunk_idx, total_chunks)

            logger.info(f"Streaming playback completed: {chunk_idx}/{total_chunks} chunks")

        finally:
            # Clean up PyAudio resources
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
            p.terminate()

    def stop_playback(self) -> None:
        """Stop ongoing streaming playback."""
        logger.info("Stopping playback")
        self._stop_playback.set()

        # Wait for playback thread to finish if it exists
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join(timeout=2.0)
            self._playback_thread = None

    def is_playing(self) -> bool:
        """Check if audio is currently playing.

        Returns:
            True if playback is ongoing, False otherwise
        """
        return (
            self._playback_thread is not None
            and self._playback_thread.is_alive()
            and not self._stop_playback.is_set()
        )

    @staticmethod
    def find_devices() -> List[usb.core.Device]:
        """Find all connected GL100 devices.

        Returns:
            List of USB device objects
        """
        devices = usb.core.find(
            find_all=True,
            idVendor=GL100Device.VENDOR_ID,
            idProduct=GL100Device.PRODUCT_ID,
        )
        return list(devices)
