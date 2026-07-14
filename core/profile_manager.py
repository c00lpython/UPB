# core/profile_manager.py

import os
import shutil
from PySide6.QtWebEngineCore import QWebEngineProfile


class ProfileManager:
    """Управляет профилями QWebEngine для каждого проекта"""
    
    @staticmethod
    def get_profile_for_project(project_name: str) -> QWebEngineProfile:
        """Создаёт или возвращает профиль для указанного проекта"""
        
        # Папка для хранения профилей проектов
        base_dir = os.path.join(os.getcwd(), "projects", project_name, "profile")
        
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        
        # Создаём профиль с именем проекта
        profile = QWebEngineProfile(project_name)
        profile.setPersistentStoragePath(base_dir)
        profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        
        # Включаем кэш и локальное хранилище
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
        
        print(f"✅ Профиль создан для {project_name}: {base_dir}")
        return profile
    
    @staticmethod
    def delete_profile_for_project(project_name: str):
        """Удаляет профиль проекта (при удалении проекта)"""
        profile_path = os.path.join(os.getcwd(), "projects", project_name, "profile")
        if os.path.exists(profile_path):
            shutil.rmtree(profile_path)
            print(f"✅ Профиль для {project_name} удалён")