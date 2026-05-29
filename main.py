import sys
import os
from PyQt6.QtWidgets import QApplication

os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "9222"

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    
    # НЕТ ГЛОБАЛЬНОГО ПРОФИЛЯ! Передаём None.
    # Профиль будет создаваться при создании/открытии проекта
    window = MainWindow(profile=None)
    window.show()
    
    print("\n" + "="*60)
    print("🔧 REMOTE DEBUGGING ACTIVE")
    print("="*60)
    print("1. Откройте Google Chrome или Edge")
    print("2. Перейдите по адресу: http://localhost:9222")
    print("3. Нажмите 'inspect' под вашей страницей")
    print("="*60 + "\n")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()