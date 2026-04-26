import sys
import os
import json
import urllib.request
import pyaudio
import numpy as np
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QComboBox, QLabel, 
                             QProgressBar, QFileDialog, QMessageBox, QSlider, QFrame)
from PySide6.QtCore import QThread, Signal, Qt, QPoint
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QAction, QIcon

APPDATA_PATH = os.path.join(os.getenv('APPDATA'), 'NoxMic')
CONFIG_FILE = os.path.join(APPDATA_PATH, 'config.json')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_path(relative_path):
    return os.path.join(BASE_DIR, relative_path)

font_path = get_path("MaterialSymbolsRounded.ttf")
icon_path = get_path("icon.ico")

class AudioStreamThread(QThread):
    volume_signal = Signal(int)
    error_signal = Signal(str)

    def __init__(self):
        super().__init__()
        self.url = ""
        self.output_device_index = None
        self.chunk_size = 1024
        self.running = False
        self.gain_factor = 1.0

    def run(self):
        self.running = True
        p = pyaudio.PyAudio()
        stream = None
        try:
            target_url = self.url.strip()
            if not target_url.startswith(('http://', 'https://')):
                target_url = 'http://' + target_url

            stream = p.open(format=pyaudio.paInt16, 
                          channels=1, 
                          rate=44100, 
                          output=True,
                          output_device_index=self.output_device_index,
                          frames_per_buffer=self.chunk_size)
            
            with urllib.request.urlopen(target_url, timeout=5) as response:
                while self.running:
                    chunk = response.read(self.chunk_size)
                    if not chunk: break
                    audio_data = np.frombuffer(chunk, dtype=np.int16).astype(np.float32)
                    audio_data *= self.gain_factor
                    audio_data = np.clip(audio_data, -32768, 32767)
                    processed_chunk = audio_data.astype(np.int16).tobytes()
                    stream.write(processed_chunk)
                    level = min(100, int(np.abs(audio_data).max() / 327))
                    self.volume_signal.emit(level)
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            self.running = False
            if stream:
                try: stream.close()
                except: pass
            p.terminate()

class NoxMicApp(QWidget):
    def __init__(self):
        super().__init__()
        self.pa = pyaudio.PyAudio()

        self.setWindowIcon(QIcon(icon_path))
        self.setWindowTitle("NoxMic")

        font_id = QFontDatabase.addApplicationFont(font_path)
        self.icon_font = QFontDatabase.applicationFontFamilies(font_id)[0] if font_id != -1 else "Arial"

        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.drag_pos = QPoint()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        self.setFixedSize(420, 560)
        
        self.setStyleSheet(f"""
            QWidget#MainFrame {{
                background-color: #0F0F0F;
                border: 1px solid #252525;
                border-radius: 6px;
            }}

            QWidget {{
                color: #B3B3B3;
                font-family: 'Segoe UI', sans-serif;
            }}
            
            QLabel[class="Symbol"] {{
                font-family: '{self.icon_font}';
                font-size: 20px;
                color: #FFFFFF;
            }}
            
            QPushButton#ActionBtn {{
                background-color: #1A1A1A;
                border: 1px solid #2A2A2A;
                border-radius: 8px;
                color: #FFFFFF;
                font-weight: 500;
                min-height: 40px;
            }}

            QPushButton#ActionBtn:hover {{ 
                background-color: #252525; 
            }}

            QFrame#TitleBar {{
                background-color: #0F0F0F;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border: none;
            }}

            QPushButton#TitleBtn {{
                font-family: '{self.icon_font}';
                background: transparent;
                border: none;
                color: #B3B3B3;
                font-size: 18px;
                margin-top: 3px;
                margin-bottom: 3px;
                border-radius: 6px; 
                max-height: 35px;
                max-width: 35px;
                min-height: 35px;
                min-width: 35px;
            }}

            QPushButton#CloseBtn {{
                font-family: '{self.icon_font}';
                background: transparent;
                border: none;
                color: #B3B3B3;
                font-size: 18px;
                margin-top: 3px;
                margin-right: 3px;
                margin-bottom: 3px;
                border-radius: 6px; 
                max-height: 35px;
                max-width: 35px;
                min-height: 35px;
                min-width: 35px;
            }}

            QPushButton#TitleBtn:hover {{ 
                background-color: #252525; 
                color: white; 
            }}

            QPushButton#CloseBtn:hover {{ 
                background-color: #E81123; 
            }}
            
            QLineEdit, QComboBox {{
                background-color: #1A1A1A;
                border: 1px solid #252525;
                border-radius: 8px;
                padding: 10px;
                color: #FFFFFF;
            }}

            QComboBox::drop-down {{ 
                border: 0; 
                width: 0px; 
            }}
            
            QPushButton#StartBtn {{
                background-color: #0078D4;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 14px;
                font-weight: bold;
            }}

            QPushButton#StartBtn:hover {{ 
                background-color: #1086E5; 
            }}

            QProgressBar {{
                background-color: #1A1A1A;
                height: 4px;
                border: none;
                border-radius: 4px;
                text-align: transparent;
            }}

            QProgressBar::chunk {{ 
                background-color: #0078D4; 
                border-radius: 4px; 
            }}
            
            QSlider::groove:horizontal {{ 
                height: 4px; 
                background: #252525; 
                border-radius: 2px; 
            }}

            QSlider::handle:horizontal {{ 
                background: #0078D4; 
                width: 14px; 
                height: 14px; 
                margin: -5px 0; 
                border-radius: 7px; 
            }}
        """)

        self.main_container = QFrame(self)
        self.main_container.setObjectName("MainFrame")
        self.main_container.setFixedSize(420, 560)
        
        root_layout = QVBoxLayout(self.main_container)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.title_bar = QFrame()
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setFixedHeight(40)
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(12, 0, 0, 0)
        title_layout.setSpacing(0)
        
        title_layout.addWidget(QLabel("NoxMic", styleSheet="font-size: 12px; font-weight: bold; color: white;"))
        title_layout.addStretch()
        
        btn_min = QPushButton("\ue15b", objectName="TitleBtn")
        btn_min.clicked.connect(self.showMinimized)
        
        btn_close = QPushButton("\ue5cd", objectName="TitleBtn")
        btn_close.setObjectName("CloseBtn")
        btn_close.clicked.connect(self.close)
        
        title_layout.addWidget(btn_min)
        title_layout.addWidget(btn_close)
        root_layout.addWidget(self.title_bar)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(25, 20, 25, 25)
        layout.setSpacing(15)

        def add_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet("color: #555555; font-size: 10px; font-weight: bold; text-transform: uppercase;")
            layout.addWidget(lbl)

        add_label("Network Source")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("http://192.168.1.15:8080/audio.wav")
        layout.addWidget(self.url_input)

        add_label("Output Device")
        self.device_box = QComboBox()
        self.refresh_devices()
        layout.addWidget(self.device_box)

        add_label("Gain Control")
        gain_layout = QHBoxLayout()
        self.gain_slider = QSlider(Qt.Horizontal)
        self.gain_slider.setRange(0, 500)
        self.gain_slider.setValue(100)
        self.gain_slider.valueChanged.connect(self.update_dsp)
        
        self.btn_reset = QPushButton("\ue042", objectName="ActionBtn")
        self.btn_reset.setStyleSheet(f"font-family: '{self.icon_font}'; font-size: 18px; width: 40px; min-height: 30px;")
        self.btn_reset.clicked.connect(lambda: self.gain_slider.setValue(100))
        
        gain_layout.addWidget(self.gain_slider)
        gain_layout.addWidget(self.btn_reset)
        layout.addLayout(gain_layout)

        add_label("Configuration")
        config_layout = QHBoxLayout()
        
        for name, icon, func in [("Import", "\ue2c4", self.import_settings), 
                                 ("Export", "\ue2c6", self.export_settings)]:
            btn = QPushButton(objectName="ActionBtn")
            btn.clicked.connect(func)
            btn_layout = QHBoxLayout(btn)
            btn_layout.setContentsMargins(15, 0, 15, 0)
            
            icon_lbl = QLabel(icon)
            icon_lbl.setProperty("class", "Symbol")
            
            btn_layout.addWidget(icon_lbl)
            btn_layout.addWidget(QLabel(name, styleSheet="color: white; font-weight: 500;"))
            btn_layout.addStretch()
            config_layout.addWidget(btn)
        
        layout.addLayout(config_layout)

        layout.addStretch()
        self.bar = QProgressBar()
        layout.addWidget(self.bar)

        self.btn_start = QPushButton("INITIALIZE STREAM")
        self.btn_start.setObjectName("StartBtn")
        self.btn_start.clicked.connect(self.toggle_stream)
        layout.addWidget(self.btn_start)

        root_layout.addWidget(content)

        self.thread = AudioStreamThread()
        self.thread.volume_signal.connect(self.bar.setValue)
        self.thread.error_signal.connect(self.show_error)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.title_bar.underMouse():
            self.drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.title_bar.underMouse():
            self.move(event.globalPosition().toPoint() - self.drag_pos)
            event.accept()

    def update_dsp(self):
        self.thread.gain_factor = self.gain_slider.value() / 100.0

    def refresh_devices(self):
        self.device_box.clear()
        try:
            p = pyaudio.PyAudio()
            default_api = p.get_default_host_api_info()['index']
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                if dev['maxOutputChannels'] > 0 and dev['hostApi'] == default_api:
                    self.device_box.addItem(dev['name'], i)
            p.terminate()
        except: pass

    def toggle_stream(self):
        if not self.thread.isRunning():
            self.save_settings()
            self.update_dsp()
            self.thread.url = self.url_input.text()
            self.thread.output_device_index = self.device_box.currentData()
            self.thread.start()
            self.btn_start.setText("Stop Stream")
            self.btn_start.setStyleSheet("background-color: #A11D1D;")
            self.toggle_action.setText("Stop Stream")
        else:
            self.thread.running = False
            self.btn_start.setText("Start Stream")
            self.btn_start.setStyleSheet("")
            self.bar.setValue(0)
            self.toggle_action.setText("Start Stream")

    def show_error(self, msg):
        QMessageBox.critical(self, "Error", msg)
        if self.thread.isRunning(): self.toggle_stream()

    def save_settings(self, path=CONFIG_FILE):
        if not os.path.exists(APPDATA_PATH): os.makedirs(APPDATA_PATH)
        data = {"url": self.url_input.text(), "dev": self.device_box.currentIndex(), "gain": self.gain_slider.value()}
        with open(path, 'w') as f: json.dump(data, f)

    def load_settings(self, path=CONFIG_FILE):
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    self.url_input.setText(data.get("url", ""))
                    self.device_box.setCurrentIndex(data.get("dev", 0))
                    self.gain_slider.setValue(data.get("gain", 100))
                    self.update_dsp()
            except: pass

    def export_settings(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export", "", "JSON (*.json)")
        if path: self.save_settings(path)

    def import_settings(self):
        path, _ = QFileDialog.getOpenFileName(self, "Import", "", "JSON (*.json)")
        if path: self.load_settings(path)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(icon_path)) 
        
        self.tray_menu = QMenu()
        
        self.toggle_action = QAction("Start Stream", self)
        self.toggle_action.triggered.connect(self.toggle_stream)
        
        open_action = QAction("Open Settings", self)
        open_action.triggered.connect(self.show_window)
        
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        self.tray_menu.addAction(self.toggle_action)
        self.tray_menu.addSeparator()
        self.tray_menu.addAction(open_action)
        self.tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.toggle_stream()

    def show_window(self):
        self.showNormal()
        self.activateWindow()

    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) 
    window = NoxMicApp()
    window.init_tray()
    sys.exit(app.exec())