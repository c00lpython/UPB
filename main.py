# main.py
import sys
import os

# ОТКЛЮЧАЕМ GPU (софтверный рендеринг)
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"
os.environ["QT_OPENGL"] = "software"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Включаем программный рендеринг OpenGL
    app.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()