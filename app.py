import sys
import json
import os
import platform
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSlider, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette, QFont
import wmi
import subprocess

CONFIG_FILE = "brightness_config.json"

class BrightnessApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mensah Eye Guard")
        self.setGeometry(300, 300, 400, 400)
        self.cpu_vendor = self.detect_cpu_vendor()
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        title_label = QLabel("Mensah Eye Guard", self)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(title_label)
        
        self.label = QLabel("Adjust Screen Brightness and Gamma", self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        brightness_layout, self.brightness_slider = self.create_slider("Brightness")
        layout.addLayout(brightness_layout)

        gamma_red_layout, self.gamma_red_slider = self.create_slider("Red Gamma")
        layout.addLayout(gamma_red_layout)

        gamma_green_layout, self.gamma_green_slider = self.create_slider("Green Gamma")
        layout.addLayout(gamma_green_layout)

        gamma_blue_layout, self.gamma_blue_slider = self.create_slider("Blue Gamma")
        layout.addLayout(gamma_blue_layout)

        self.save_button = QPushButton("Save Settings", self)
        self.save_button.setStyleSheet("padding: 8px; font-size: 14px;")
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button)
        
        self.setLayout(layout)

    def create_slider(self, label_text):
        layout = QVBoxLayout()
        label = QLabel(label_text, self)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        slider = QSlider(Qt.Horizontal, self)
        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setValue(50)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTickInterval(10)
        layout.addWidget(slider)

        if "Brightness" in label_text:
            slider.valueChanged.connect(self.set_brightness)
        else:
            slider.setMinimum(10)
            slider.setMaximum(300)
            slider.setValue(100)
            slider.setTickInterval(30)
            slider.valueChanged.connect(self.adjust_gamma)

        slider.setFixedWidth(300)
        return layout, slider

    def detect_cpu_vendor(self):
        cpu_info = platform.processor()
        if "Intel" in cpu_info:
            return "Intel"
        elif "AMD" in cpu_info or "amd" in cpu_info.lower():
            return "AMD"
        else:
            return "Unknown"

    def get_current_brightness(self):
        try:
            if platform.system() == "Windows":
                w = wmi.WMI(namespace='wmi')
                brightness_levels = w.WmiMonitorBrightness()[0]
                return brightness_levels.CurrentBrightness
            else:
                return 50
        except Exception as e:
            self.label.setText(f"Error: {e}")
            return 50

    def set_brightness(self):
        try:
            new_brightness = self.brightness_slider.value()
            if platform.system() == "Windows":
                w = wmi.WMI(namespace='wmi')
                brightness_methods = w.WmiMonitorBrightnessMethods()[0]
                brightness_methods.WmiSetBrightness(new_brightness, 0)
                self.label.setText(f"Brightness set to {new_brightness}%")
            elif platform.system() == "Linux" and self.cpu_vendor == "AMD":
                self.set_amd_brightness(new_brightness)
            elif platform.system() == "Linux" and self.cpu_vendor == "Intel":
                self.set_intel_brightness(new_brightness)
            else:
                self.label.setText("Brightness adjustment not supported on this platform.")
        except Exception as e:
            self.label.setText(f"Error: {e}")

    def set_amd_brightness(self, brightness):
        if self.check_xrandr():
            try:
                subprocess.run(["xrandr", "--output", "HDMI-1", "--brightness", str(brightness / 100)], check=True)
            except subprocess.CalledProcessError as e:
                self.label.setText(f"Failed to set AMD brightness: {e}")
            except Exception as e:
                self.label.setText(f"Error setting AMD brightness: {e}")
        else:
            self.label.setText("xrandr command not found. Please install xrandr to adjust brightness.")

    def set_intel_brightness(self, brightness):
        try:
            subprocess.run(["echo", f"Setting Intel brightness to {brightness}%"], check=True)
        except Exception as e:
            self.label.setText(f"Error setting Intel brightness: {e}")

    def adjust_gamma(self):
        red_gamma = self.gamma_red_slider.value() / 100.0
        green_gamma = self.gamma_green_slider.value() / 100.0
        blue_gamma = self.gamma_blue_slider.value() / 100.0
        
        if platform.system() == "Linux" and self.check_xrandr():
            try:
                subprocess.run(
                    ["xrandr", "--output", "HDMI-1", "--gamma", f"{red_gamma}:{green_gamma}:{blue_gamma}"],
                    check=True
                )
                self.label.setText(f"Gamma set to R: {red_gamma}, G: {green_gamma}, B: {blue_gamma}")
            except subprocess.CalledProcessError as e:
                self.label.setText(f"Failed to set gamma: {e}")
            except Exception as e:
                self.label.setText(f"Error setting gamma: {e}")
        else:
            self.label.setText("Gamma adjustment not supported or xrandr not found.")

    def check_xrandr(self):
        try:
            subprocess.run(["xrandr", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except FileNotFoundError:
            return False
        except subprocess.CalledProcessError:
            return False

    def save_settings(self):
        settings = {
            "brightness": self.brightness_slider.value(),
            "gamma_red": self.gamma_red_slider.value(),
            "gamma_green": self.gamma_green_slider.value(),
            "gamma_blue": self.gamma_blue_slider.value()
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(settings, f)
        self.label.setText("Settings saved!")

    def load_settings(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                settings = json.load(f)
                self.brightness_slider.setValue(settings.get("brightness", 50))
                self.gamma_red_slider.setValue(settings.get("gamma_red", 100))
                self.gamma_green_slider.setValue(settings.get("gamma_green", 100))
                self.gamma_blue_slider.setValue(settings.get("gamma_blue", 100))
                self.adjust_gamma()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BrightnessApp()
    window.show()
    sys.exit(app.exec())
