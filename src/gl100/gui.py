"""PyQt6 GUI for GL100 Manager.

This module provides the graphical user interface for managing the GL100 looper pedal.
"""

import sys
import logging
from typing import Optional
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QFileDialog,
    QMessageBox,
    QProgressBar,
    QStatusBar,
    QHeaderView,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
import numpy as np
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

from gl100.usb_device import GL100Device
from gl100.protocol import GL100Protocol, TrackInfo


logger = logging.getLogger(__name__)


class GL100Worker(QThread):
    """Worker thread for GL100 operations to prevent UI blocking."""

    finished = pyqtSignal()
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)  # (current, total) bytes
    track_list_ready = pyqtSignal(list)
    track_downloaded = pyqtSignal(np.ndarray)

    def __init__(self, device: GL100Device):
        super().__init__()
        self.device = device
        self.operation = None
        self.params = {}

    def set_operation(self, operation: str, **params):
        """Set the operation to perform."""
        self.operation = operation
        self.params = params

    def run(self):
        """Execute the operation in background thread."""
        try:
            if self.operation == "list_tracks":
                tracks = self.device.list_tracks()
                self.track_list_ready.emit(tracks)

            elif self.operation == "download":
                slot = self.params["slot"]

                def progress_callback(current: int, total: int) -> None:
                    self.progress.emit(current, total)

                audio = self.device.download_track(slot, progress_callback)
                self.track_downloaded.emit(audio)

            elif self.operation == "upload":
                slot = self.params["slot"]
                audio = self.params["audio"]

                def progress_callback(current: int, total: int) -> None:
                    self.progress.emit(current, total)

                self.device.upload_track(slot, audio, progress_callback)

            elif self.operation == "delete":
                slot = self.params["slot"]
                self.device.delete_track(slot)

            elif self.operation == "play":
                slot = self.params["slot"]

                def progress_callback(current: int, total: int) -> None:
                    self.progress.emit(current, total)

                # Use streaming playback for real-time audio
                self.device.play_track_streaming(slot, progress_callback)

            self.finished.emit()

        except Exception as e:
            logger.error(f"Operation {self.operation} failed: {e}")
            self.error.emit(str(e))


class GL100MainWindow(QMainWindow):
    """Main window for GL100 Manager application."""

    def __init__(self):
        super().__init__()
        self.device = GL100Device()
        self.worker: Optional[GL100Worker] = None
        self.current_slot = -1
        self.downloaded_audio: Optional[np.ndarray] = None
        self.play_buttons = {}  # Store references to play buttons
        self.current_playing_slot: Optional[int] = None  # Track which slot is playing

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Mooer Looper Manager")
        self.setGeometry(100, 100, 1000, 700)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Connection controls
        connection_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect to GL100")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.status_label = QLabel("Not connected")
        self.refresh_btn = QPushButton("Refresh Track List")
        self.refresh_btn.clicked.connect(self.refresh_tracks)
        self.refresh_btn.setEnabled(False)

        connection_layout.addWidget(self.connect_btn)
        connection_layout.addWidget(self.status_label)
        connection_layout.addStretch()
        connection_layout.addWidget(self.refresh_btn)

        main_layout.addLayout(connection_layout)

        # Track table
        self.track_table = QTableWidget()
        self.track_table.setColumnCount(4)
        self.track_table.setHorizontalHeaderLabels(
            ["Status", "Duration", "Size", "Actions"]
        )
        self.track_table.setRowCount(GL100Protocol.MAX_TRACKS)
        self.track_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.track_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.track_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Initialize table with slot numbers
        for i in range(GL100Protocol.MAX_TRACKS):
            # Vertical header shows slot number
            self.track_table.setVerticalHeaderItem(i, QTableWidgetItem(f"{i}"))
            
            self.track_table.setItem(i, 0, QTableWidgetItem("Unknown"))
            self.track_table.setItem(i, 1, QTableWidgetItem("-"))
            self.track_table.setItem(i, 2, QTableWidgetItem("-"))

            # Action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(4, 2, 4, 2)
            action_layout.setSpacing(4)

            download_btn = QPushButton("Download")
            download_btn.setMinimumWidth(80)
            download_btn.clicked.connect(lambda checked, slot=i: self.download_track(slot))
            
            upload_btn = QPushButton("Upload")
            upload_btn.setMinimumWidth(70)
            upload_btn.clicked.connect(lambda checked, slot=i: self.upload_track(slot))
            
            delete_btn = QPushButton("Delete")
            delete_btn.setMinimumWidth(70)
            delete_btn.clicked.connect(lambda checked, slot=i: self.delete_track(slot))
            
            play_btn = QPushButton("Play")
            play_btn.setMinimumWidth(60)
            play_btn.clicked.connect(lambda checked, slot=i: self.play_track(slot))
            self.play_buttons[i] = play_btn

            action_layout.addWidget(download_btn)
            action_layout.addWidget(upload_btn)
            action_layout.addWidget(delete_btn)
            action_layout.addWidget(play_btn)

            self.track_table.setCellWidget(i, 3, action_widget)

        # Set specific minimum width for the actions column
        self.track_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.track_table.setColumnWidth(3, 320)

        main_layout.addWidget(self.track_table)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def toggle_connection(self):
        """Connect or disconnect from the device."""
        if self.device.is_connected():
            self.device.disconnect()
            self.connect_btn.setText("Connect to GL100")
            self.status_label.setText("Not connected")
            self.refresh_btn.setEnabled(False)
            self.status_bar.showMessage("Disconnected")
        else:
            if self.device.connect():
                self.connect_btn.setText("Disconnect")
                self.status_label.setText("Connected")
                self.status_label.setStyleSheet("color: green")
                self.refresh_btn.setEnabled(True)
                self.status_bar.showMessage("Connected to GL100")
                self.refresh_tracks()
            else:
                QMessageBox.critical(
                    self,
                    "Connection Error",
                    "Failed to connect to GL100 device.\n"
                    "Make sure the device is plugged in and you have proper permissions.",
                )

    def refresh_tracks(self):
        """Refresh the track list from the device."""
        if not self.device.is_connected():
            return

        self.status_bar.showMessage("Refreshing track list...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate

        self.worker = GL100Worker(self.device)
        self.worker.set_operation("list_tracks")
        self.worker.track_list_ready.connect(self.update_track_list)
        self.worker.finished.connect(lambda: self.progress_bar.setVisible(False))
        self.worker.error.connect(self.show_error)
        self.worker.start()

    def update_track_list(self, tracks: list):
        """Update the track table with track information."""
        for track in tracks:
            status = "Has Track" if track.has_track else "Empty"

            # Format duration as mm:ss
            if track.has_track:
                minutes = int(track.duration // 60)
                seconds = int(track.duration % 60)
                duration = f"{minutes:02d}:{seconds:02d}"
            else:
                duration = "-"

            size = f"{track.size / (1024 * 1024):.2f} MB" if track.has_track else "-"

            self.track_table.setItem(track.slot, 0, QTableWidgetItem(status))
            self.track_table.setItem(track.slot, 1, QTableWidgetItem(duration))
            self.track_table.setItem(track.slot, 2, QTableWidgetItem(size))

            # Color code the row
            color = QColor(200, 255, 200) if track.has_track else QColor(255, 255, 255)
            for col in range(4):
                item = self.track_table.item(track.slot, col)
                if item:
                    item.setBackground(color)

        self.status_bar.showMessage("Track list updated")

    def download_track(self, slot: int):
        """Download a track from the device."""
        if not self.device.is_connected():
            return

        self.current_slot = slot
        self.status_bar.showMessage(f"Downloading track {slot}...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)  # Will update with real values
        self.progress_bar.setValue(0)

        self.worker = GL100Worker(self.device)
        self.worker.set_operation("download", slot=slot)
        self.worker.track_downloaded.connect(self.save_downloaded_track)
        self.worker.progress.connect(self.update_download_progress)
        self.worker.finished.connect(lambda: self.progress_bar.setVisible(False))
        self.worker.error.connect(self.show_error)
        self.worker.start()

    def update_download_progress(self, current: int, total: int) -> None:
        """Update download progress bar."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            # Show size in MB
            current_mb = current / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self.status_bar.showMessage(
                f"Downloading track {self.current_slot}... {current_mb:.2f}/{total_mb:.2f} MB"
            )
        else:
            # Fallback to indeterminate if total is unknown
            self.progress_bar.setRange(0, 0)

    def save_downloaded_track(self, audio: np.ndarray):
        """Save downloaded audio to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Track",
            f"track_{self.current_slot}.wav",
            "WAV files (*.wav);;All files (*.*)",
        )

        if file_path:
            try:
                # Save as WAV using scipy or soundfile
                import scipy.io.wavfile as wav

                wav.write(file_path, 44100, audio)
                self.status_bar.showMessage(f"Track {self.current_slot} saved to {file_path}")
                QMessageBox.information(self, "Success", f"Track saved to {file_path}")
            except Exception as e:
                self.show_error(f"Failed to save file: {e}")

    def upload_track(self, slot: int):
        """Upload a track to the device."""
        if not self.device.is_connected():
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio File",
            "",
            "Audio files (*.wav *.mp3 *.flac *.ogg *.m4a *.wma *.aac);;All files (*.*)",
        )

        if not file_path:
            return

        try:
            self.current_slot = slot
            self.status_bar.showMessage(f"Processing audio file...")
            
            # Use pydub if available for robust format support
            if PYDUB_AVAILABLE:
                try:
                    audio_segment = AudioSegment.from_file(file_path)
                    
                    # Resample if needed
                    if audio_segment.frame_rate != 44100:
                        self.status_bar.showMessage(f"Resampling from {audio_segment.frame_rate}Hz to 44100Hz...")
                        audio_segment = audio_segment.set_frame_rate(44100)
                    
                    # Convert to numpy array
                    # get_array_of_samples returns array.array
                    samples = np.array(audio_segment.get_array_of_samples())
                    
                    # Handle channels
                    if audio_segment.channels == 2:
                        # Reshape to (frames, 2)
                        audio = samples.reshape((-1, 2))
                    else:
                        # Mono (frames,)
                        audio = samples
                        
                    # Pydub usually works in int16 or whatever the source is
                    # The protocol handles int16/int32 conversion and mono duplication
                    
                except Exception as e:
                    # Fallback or error if ffmpeg missing
                    if "ffmpeg" in str(e).lower() or "avconv" in str(e).lower():
                        raise RuntimeError("FFmpeg is required for format conversion. Please install ffmpeg.")
                    raise e
            else:
                # Fallback to scipy for WAV only
                import scipy.io.wavfile as wav
                sample_rate, audio = wav.read(file_path)
                if sample_rate != 44100:
                     raise RuntimeError(f"Sample rate {sample_rate}Hz not supported without pydub/ffmpeg. Please convert to 44.1kHz or install ffmpeg.")

            self.status_bar.showMessage(f"Uploading to slot {slot}...")
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)

            self.worker = GL100Worker(self.device)
            self.worker.set_operation("upload", slot=slot, audio=audio)
            self.worker.progress.connect(self.update_upload_progress)
            self.worker.finished.connect(self.on_upload_complete)
            self.worker.error.connect(self.show_error)
            self.worker.start()

        except Exception as e:
            self.show_error(f"Failed to load audio file: {e}")

    def on_upload_complete(self):
        """Handle upload completion."""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"Upload to slot {self.current_slot} complete")
        QMessageBox.information(self, "Success", f"Track uploaded to slot {self.current_slot}")
        self.refresh_tracks()

    def update_upload_progress(self, current: int, total: int) -> None:
        """Update upload progress bar."""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            current_mb = current / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self.status_bar.showMessage(
                f"Uploading track {self.current_slot}... {current_mb:.2f}/{total_mb:.2f} MB"
            )
        else:
            self.progress_bar.setRange(0, 0)

    def delete_track(self, slot: int):
        """Delete a track from the device."""
        if not self.device.is_connected():
            return

        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete track {slot}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.current_slot = slot
            self.status_bar.showMessage(f"Deleting track {slot}...")

            self.worker = GL100Worker(self.device)
            self.worker.set_operation("delete", slot=slot)
            self.worker.finished.connect(self.on_delete_complete)
            self.worker.error.connect(self.show_error)
            self.worker.start()

    def on_delete_complete(self):
        """Handle delete completion."""
        self.status_bar.showMessage(f"Track {self.current_slot} deleted")
        QMessageBox.information(self, "Success", f"Track {self.current_slot} deleted")
        self.refresh_tracks()

    def play_track(self, slot: int):
        """Play/pause a track on the device."""
        if not self.device.is_connected():
            return

        # If this slot is already playing, stop it
        if self.current_playing_slot == slot:
            self.stop_playback()
            return

        # If another slot is playing, stop it first
        if self.current_playing_slot is not None:
            self.stop_playback()

        # Update state
        self.current_playing_slot = slot
        if slot in self.play_buttons:
            self.play_buttons[slot].setText("Stop")

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage(f"Starting playback of track {slot}...")

        self.worker = GL100Worker(self.device)
        self.worker.set_operation("play", slot=slot)

        # Connect signals
        def on_finished():
            # Only reset UI if this slot is still the active one (i.e. finished naturally)
            if self.current_playing_slot == slot:
                self.progress_bar.setVisible(False)
                if slot in self.play_buttons:
                    self.play_buttons[slot].setText("Play")
                self.current_playing_slot = None
                self.status_bar.showMessage(f"Finished playing track {slot}")

        def on_progress(current, total):
            if total > 0:
                percent = int((current / total) * 100)
                self.progress_bar.setValue(percent)
                self.status_bar.showMessage(
                    f"Playing track {slot}: {current}/{total} chunks ({percent}%)"
                )

        self.worker.finished.connect(on_finished)
        self.worker.progress.connect(on_progress)
        self.worker.error.connect(self.show_error)
        self.worker.start()

    def stop_playback(self):
        """Stop ongoing audio playback."""
        if not self.device.is_connected():
            return

        self.device.stop_playback()
        
        # Reset UI for the currently playing slot
        if self.current_playing_slot is not None:
            slot = self.current_playing_slot
            if slot in self.play_buttons:
                self.play_buttons[slot].setText("Play")
            self.current_playing_slot = None
            
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Playback stopped")

    def show_error(self, error_msg: str):
        """Display error message to user."""
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage(f"Error: {error_msg}")
        QMessageBox.critical(self, "Error", error_msg)

    def closeEvent(self, event):
        """Handle window close event."""
        if self.device.is_connected():
            self.device.disconnect()
        event.accept()


def main():
    """Main entry point for the GUI application."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    app = QApplication(sys.argv)
    window = GL100MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
