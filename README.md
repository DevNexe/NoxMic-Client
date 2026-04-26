# NoxMic Pro

A minimalist, high-performance network audio streamer inspired by the NoxPlayer interface. This application allows you to receive high-quality audio streams over the network and output them to a virtual or physical audio device with real-time gain control.

## 🚀 Features

- **Modern UI**: Dark-themed, frameless interface built with PySide6 and Material Symbols.
- **Real-time Streaming**: Low-latency audio processing using PyAudio and NumPy.
- **DSP Gain Control**: Adjust audio volume on the fly (up to 500% gain).
- **Tray Integration**:
  - Starts minimized to tray by default.
  - Custom context menu for quick control.
  - Left-click on tray icon to toggle stream (Start/Stop).
- **Configuration Management**: Import and export your stream settings (URL, Device, Gain) as JSON files.
- **Cross-Platform Ready**: Designed to be compiled for both Windows and Linux.

## 🛠 Tech Stack

- **Python 3.11+**
- **PySide6** (Qt for Python)
- **PyAudio** (PortAudio bindings)
- **NumPy** (Digital Signal Processing)
- **Nuitka** (C++ compilation for performance)

## 📦 Installation

### 1. Prerequisites
Ensure you have Python 3.11 installed. You might also need PortAudio development headers for your OS.

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install libportaudio2 portaudio19-dev libasound2-dev
2. Setup
Clone the repository and install dependencies:

Bash
pip install -r requirements.txt
🔨 Compilation (Nuitka)
To compile the application into a single executable file with all assets included:

Windows:

Bash
python -m nuitka --standalone --onefile --enable-plugin=pyside6 --windows-disable-console --windows-icon-from-ico=icon.ico --include-data-files="MaterialSymbolsRounded.ttf=." --include-data-files="icon.png=." main.py
🤖 GitHub Actions
This project includes a .github/workflows/release.yml file. It automatically builds and creates a new release with Windows (.exe) and Linux (.bin) binaries whenever you push a new tag:

Bash
git tag v1.0.0
git push origin v1.0.0
📄 License
This project is open-source and available under the MIT License.