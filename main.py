# main.py
import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.n8n_server import N8nServer


def main():
    app = QApplication(sys.argv)
    
    # Запускаем n8n в фоновом режиме (не блокирует)
    n8n_server = N8nServer()
    n8n_server.start()
    
    # Создаём и показываем окно
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()