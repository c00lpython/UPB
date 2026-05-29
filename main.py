# main.py
import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWebEngineCore import QWebEngineProfile

# 1. ВКЛЮЧАЕМ УДАЛЕННУЮ ОТЛАДКУ ГЛОБАЛЬНО ДЛЯ ВСЕХ ВКЛАДОК
os.environ["QTWEBENGINE_REMOTE_DEBUGGING"] = "9222"

from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)

    # 2. СОЗДАЕМ ПРОФИЛЬ ДЛЯ ПРОЕКТА
    # Это решит проблему с сохранением сессии и куками для всех вкладок
    default_profile = QWebEngineProfile("UPB_Default")
    default_profile.setPersistentStoragePath("profiles/default")
    default_profile.setPersistentCookiesPolicy(
        QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
    )

    window = MainWindow(default_profile)
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