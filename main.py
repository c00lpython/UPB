# main.py
import sys
import os
import signal

# ОТКЛЮЧАЕМ GPU (софтверный рендеринг)
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"
os.environ["QT_OPENGL"] = "software"

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from ui.main_window import MainWindow


def load_stylesheet() -> str:
    """Загружает стили из файла style.qss"""
    style_path = os.path.join(os.path.dirname(__file__), "style.qss")
    if os.path.exists(style_path):
        with open(style_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def signal_handler(signum, frame):
    """Обработчик Ctrl+C для корректного завершения"""
    print("\n🛑 Received interrupt signal. Shutting down...")
    QApplication.quit()


def main():
    # Регистрируем обработчик сигнала
    signal.signal(signal.SIGINT, signal_handler)
    
    app = QApplication(sys.argv)
    
    # Включаем программный рендеринг OpenGL
    app.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)
    
    # Загружаем стили
    stylesheet = load_stylesheet()
    if stylesheet:
        app.setStyleSheet(stylesheet)
        print("✅ Styles loaded successfully!")
    else:
        print("⚠️ No style.qss found, using default styles")
    
    window = MainWindow()
    window.show()
    
    # Таймер для обработки событий при завершении
    def on_quit():
        print("👋 Application quitting...")
    
    app.aboutToQuit.connect(on_quit)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()