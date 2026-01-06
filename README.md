# Python Mooer Looper Manager POC

**Note: This is a Python proof-of-concept project.** For the final C++ implementation with better performance and native AppImage support, see [https://github.com/shpala/MooerLooperManager](https://github.com/shpala/MooerLooperManager).

**Linux-native manager for Mooer GL100/GL200 loopers. Upload, download, and manage tracks without Windows.**

This is an open-source, cross-platform GUI application for managing Mooer looper pedals (GL100, GL200). It provides a native solution for Linux users (Mooer doesn't provide any official Linux support) and works as a lightweight alternative on Windows and macOS.

## Motivation

I don't own a Windows machine—my main machine runs Arch Linux—and Mooer doesn't provide any official software for Linux. I didn't want to deal with booting a Windows VM every time I needed to upload a backing track or download a loop from my pedal.

I have the Mooer GL100, and this tool was reverse-engineered and tested using that device. I also own gear that supports MIDI sync, which the GL100 lacks, so I'm considering upgrading to the GL200 that does support MIDI. That's why the protocol implementation is flexible enough to support both devices.

Instead of dealing with Windows, I reverse-engineered the USB protocol and built a native Linux tool.

## Features

- Native Linux support (Mooer doesn't provide an official Linux application)
- Track management: view, upload, download, and delete tracks across all 100 slots
- Automatic audio conversion: converts WAV, MP3, FLAC, OGG, etc. to the device's native 24-bit 44.1kHz stereo format
- Real-time streaming playback from device to computer
- Cross-platform: works on Windows and macOS as a lightweight open-source alternative

## Compatibility

- Mooer GL100: Fully tested and verified
- Mooer GL200: Compatible (protocol is identical)
  - Note: If your GL200 isn't detected, you may need to update the `PRODUCT_ID` in `src/gl100/usb_device.py` to match your device's USB PID

## Installation & Usage

### Prerequisites
- Python 3.8+
- libusb (usually installed by default on Linux)
- portaudio (for playback: libportaudio2 or portaudio19-dev)
- ffmpeg (optional, for MP3/FLAC conversion and resampling)

### Quick Start

The `run.sh` script sets up a virtual environment, installs dependencies, and launches the application:

```bash
chmod +x run.sh
./run.sh
```

### Manual Installation

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
PyMooerLooperManager
```

### Linux USB Permissions

To access the USB device without root, install the provided udev rule:

```bash
sudo cp 60-mooer-gl100.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

## Cross-Platform Support

While official software exists for Windows and macOS, this tool works as an open-source alternative. USB hardware access requires specific setup on these systems.

### Windows
1. Driver Setup: You may need to replace the device driver with WinUSB using [Zadig](https://zadig.akeo.ie/) for the application to detect the device.
   - Note: This might break compatibility with the official Mooer software until you restore the original driver.
2. Running: The `run.sh` script works in Git Bash or WSL. For Command Prompt/PowerShell, install Python manually and run:
   ```cmd
   pip install -r requirements.txt
   pip install -e .
   PyMooerLooperManager
   ```

### macOS
1. Dependencies: Install libusb using Homebrew:
   ```bash
   brew install libusb
   ```
2. Running: The `run.sh` script works natively in the Terminal.

## Protocol Implementation Details

The application communicates with the device using a custom vendor-specific USB protocol:

- Vendor ID: 0x34DB
- Product ID: 0x0008 (GL100)
  - GL200 users: Check your specific Product ID using `lsusb` or Device Manager
- Endpoints:
  - 0x02 (OUT): Commands
  - 0x83 (IN): Data (audio, track info)
  - 0x81 (IN): Status

### Command Structure

Commands use a 64-byte packet format with a 3-byte header (0x3F 0xAA 0x55) and a CRC-16 checksum.

### Technical Notes

Audio Format: The device uses 24-bit PCM stereo audio at 44.1 kHz. The application handles conversion from standard WAV/MP3 formats.

Frame Alignment: USB transfer chunks (1024 bytes) aren't aligned with the 24-bit stereo frame size (6 bytes). The application implements a buffering mechanism to handle the 4-byte remainder per chunk, ensuring correct channel alignment.

Mono Handling: Mono input files are automatically converted to stereo with -3dB attenuation to match the device's output behavior.

## Reverse Engineering Documentation

For details on how the USB protocol was reverse-engineered, including packet captures and analysis tools, check the [reverse_engineering](./reverse_engineering) directory.

## Known Limitations

Firmware Updates: Not supported. This project is built by reverse-engineering the protocol, and I have no intention of touching the firmware update logic—I quite like my GL100 and would prefer it not to become a very expensive paperweight.

## License

MIT License
