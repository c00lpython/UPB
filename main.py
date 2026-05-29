import sys
import threading
import time
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.n8n_server import N8nServer

def main():
    app = QApplication(sys.argv)
    
    # Запускаем n8n сервер в отдельном потоке
    n8n_server = N8nServer()
    n8n_server.start()
    
    # Ждём запуска сервера
    for _ in range(30):
        time.sleep(1)
        if n8n_server.is_running:
            break
    
    window = MainWindow(n8n_server=n8n_server)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()