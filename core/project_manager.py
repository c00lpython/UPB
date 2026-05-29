import json
import os
import shutil
import openpyxl
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal


class ProjectManager(QObject):
    """Управляет сохранением и загрузкой проектов"""
    
    project_loaded = pyqtSignal(dict)
    project_saved = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.current_project = None
        self.projects_dir = "projects"
        
        if not os.path.exists(self.projects_dir):
            os.makedirs(self.projects_dir)
    
    def get_all_projects(self):
        """Возвращает список всех проектов"""
        projects = []
        if os.path.exists(self.projects_dir):
            for item in os.listdir(self.projects_dir):
                project_path = os.path.join(self.projects_dir, item)
                if os.path.isdir(project_path) and os.path.exists(os.path.join(project_path, "metadata.json")):
                    # Загружаем метаданные для отображения
                    try:
                        with open(os.path.join(project_path, "metadata.json"), 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                        projects.append({
                            "name": item,
                            "created": meta.get("created", ""),
                            "modified": meta.get("modified", ""),
                            "variables_count": meta.get("variables_count", 0)
                        })
                    except:
                        projects.append({"name": item, "created": "", "modified": "", "variables_count": 0})
        return projects
    
    def create_project(self, name: str):
        """Создаёт новый проект"""
        project_path = os.path.join(self.projects_dir, name)
        
        if os.path.exists(project_path):
            return False, "Project already exists"
        
        os.makedirs(project_path)
        os.makedirs(os.path.join(project_path, "parser"))
        
        now = datetime.now().isoformat()
        
        # metadata.json
        metadata = {
            "name": name,
            "created": now,
            "modified": now,
            "version": "1.0",
            "variables_count": 0
        }
        with open(os.path.join(project_path, "metadata.json"), 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
        
        # browser_data.json
        browser_data = {
            "tabs": [{"url": "https://google.com", "title": "Google", "active": True}],
            "current_tab": 0,
            "history": []
        }
        with open(os.path.join(project_path, "browser_data.json"), 'w', encoding='utf-8') as f:
            json.dump(browser_data, f, indent=4, ensure_ascii=False)
        
        # config.conf
        config_content = """[OUTPUT]
format = excel
excel_path = output.xlsx
telegram_bot_token = 
telegram_chat_id = 

[PARSER]
headless = false
timeout = 10
"""
        with open(os.path.join(project_path, "config.conf"), 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        # variables.xlsx (пустой)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Variables"
        ws.append(["Name", "XPath/CSS", "Type", "URL", "Sample Text"])
        wb.save(os.path.join(project_path, "variables.xlsx"))
        
        self.current_project = name
        return True, project_path
    
    def save_project(self, name: str, variables_data: list, browser_data: dict):
        """Сохраняет текущее состояние проекта"""
        project_path = os.path.join(self.projects_dir, name)
        
        if not os.path.exists(project_path):
            return False, "Project not found"
        
        now = datetime.now().isoformat()
        
        # Обновляем metadata.json
        metadata_path = os.path.join(project_path, "metadata.json")
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        metadata["modified"] = now
        metadata["variables_count"] = len(variables_data)
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
        
        # Сохраняем browser_data.json
        with open(os.path.join(project_path, "browser_data.json"), 'w', encoding='utf-8') as f:
            json.dump(browser_data, f, indent=4, ensure_ascii=False)
        
        # Сохраняем variables.xlsx
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Variables"
        ws.append(["Name", "XPath/CSS", "Type", "URL", "Sample Text"])
        
        for var in variables_data:
            ws.append([
                var.get('name', ''),
                var.get('xpath', ''),
                var.get('type', 'Static'),
                var.get('url', ''),
                var.get('sample', '')
            ])
        
        wb.save(os.path.join(project_path, "variables.xlsx"))
        
        self.current_project = name
        return True, "Project saved"
    
    def load_project(self, name: str):
        """Загружает проект"""
        project_path = os.path.join(self.projects_dir, name)
        
        if not os.path.exists(project_path):
            return None, "Project not found"
        
        # Загружаем metadata.json
        with open(os.path.join(project_path, "metadata.json"), 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Загружаем variables.xlsx
        variables = []
        xlsx_path = os.path.join(project_path, "variables.xlsx")
        if os.path.exists(xlsx_path):
            wb = openpyxl.load_workbook(xlsx_path)
            ws = wb.active
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[0]:  # Если есть имя
                    variables.append({
                        'name': row[0] or '',
                        'xpath': row[1] or '',
                        'type': row[2] or 'Static',
                        'url': row[3] or '',
                        'sample': row[4] or ''
                    })
        
        # Загружаем browser_data.json
        browser_data = {"tabs": [], "current_tab": 0, "history": []}
        browser_path = os.path.join(project_path, "browser_data.json")
        if os.path.exists(browser_path):
            with open(browser_path, 'r', encoding='utf-8') as f:
                browser_data = json.load(f)
        
        # Загружаем config.conf
        config = {}
        config_path = os.path.join(project_path, "config.conf")
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config_text = f.read()
                # Простой парсинг конфига
                for line in config_text.split('\n'):
                    if '=' in line and not line.startswith('['):
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        
        self.current_project = name
        
        return {
            "metadata": metadata,
            "variables": variables,
            "browser_data": browser_data,
            "config": config
        }, "Loaded"
    
    def delete_project(self, name: str):
        """Удаляет проект"""
        project_path = os.path.join(self.projects_dir, name)
        
        if os.path.exists(project_path):
            shutil.rmtree(project_path)
            return True, "Project deleted"
        
        return False, "Project not found"
    
    def generate_parser(self, name: str, variables: list, config: dict):
        """Генерирует парсер в папку parser/"""
        project_path = os.path.join(self.projects_dir, name)
        parser_dir = os.path.join(project_path, "parser")
        
        if not os.path.exists(parser_dir):
            os.makedirs(parser_dir)
        
        # Генерируем код парсера
        parser_code = self._generate_parser_code(name, variables, config)
        
        parser_file = os.path.join(parser_dir, f"{name}Parser.py")
        with open(parser_file, 'w', encoding='utf-8') as f:
            f.write(parser_code)
        
        return parser_file
    
    def _generate_parser_code(self, name: str, variables: list, config: dict):
        """Генерирует Python код парсера"""
        # TODO: Реализовать генерацию
        return f"""# {name}Parser.py
# Generated by UPB

import time
from selenium import webdriver

def main():
    print("Parser: {name}")
    print(f"Variables to extract: {len(variables)}")
    
if __name__ == "__main__":
    main()
"""