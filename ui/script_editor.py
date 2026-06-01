# ui/script_editor.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QMessageBox, QInputDialog, QFileDialog
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QDateTime, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile
import os
import json
import re
import tempfile
import requests
from datetime import datetime


class ScriptEditor(QWidget):
    """Script Editor — встроенный n8n браузер + панель инструментов"""
    
    log_signal = pyqtSignal(str)
    
    def __init__(self, project_manager=None, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.n8n_url = "http://localhost:5678"
        self.current_project = None
        self.n8n_status = False
        self.init_ui()
        self.check_n8n_status()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Верхняя панель (навигация)
        top_panel = self.create_top_panel()
        layout.addLayout(top_panel)
        
        # Браузер (растягивается на всё свободное место)
        browser_panel = self.create_browser_panel()
        layout.addWidget(browser_panel, 1)
        
        # Нижняя панель (кнопки + консоль)
        bottom_panel = self.create_bottom_panel()
        layout.addWidget(bottom_panel)
    
    def create_top_panel(self):
        """Верхняя панель с навигацией"""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        self.btn_back = QPushButton("◀")
        self.btn_forward = QPushButton("▶")
        self.btn_reload = QPushButton("🔄")
        self.btn_new_workflow = QPushButton("➕ New Workflow")
        
        for btn in [self.btn_back, self.btn_forward, self.btn_reload]:
            btn.setMaximumWidth(35)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3c3c3c;
                    color: #cccccc;
                    border: 1px solid #787878;
                    border-radius: 3px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #4c4c4c;
                }
            """)
        
        self.btn_new_workflow.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        
        self.btn_back.clicked.connect(lambda: self.n8n_browser.back())
        self.btn_forward.clicked.connect(lambda: self.n8n_browser.forward())
        self.btn_reload.clicked.connect(lambda: self.n8n_browser.reload())
        self.btn_new_workflow.clicked.connect(self.create_new_workflow)
        
        self.url_label = QLabel(self.n8n_url)
        self.url_label.setStyleSheet("""
            QLabel {
                background-color: #3c3c3c;
                color: #cccccc;
                padding: 5px;
                border: 1px solid #787878;
                border-radius: 3px;
            }
        """)
        
        layout.addWidget(self.btn_back)
        layout.addWidget(self.btn_forward)
        layout.addWidget(self.btn_reload)
        layout.addWidget(self.url_label, 1)
        layout.addWidget(self.btn_new_workflow)
        
        return layout
    
    def create_browser_panel(self):
        """Панель с браузером для n8n"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Браузер
        profile = QWebEngineProfile("n8n_editor")
        profile.setPersistentStoragePath(os.path.join(tempfile.gettempdir(), "n8n_editor_profile"))
        
        self.n8n_browser = QWebEngineView()
        self.n8n_browser.setUrl(QUrl(self.n8n_url))
        self.n8n_browser.urlChanged.connect(self.on_url_changed)
        self.n8n_browser.loadFinished.connect(self.on_load_finished)
        
        layout.addWidget(self.n8n_browser, 1)
        
        return panel
    
    def create_bottom_panel(self):
        """Нижняя панель с кнопками и консолью"""
        panel = QWidget()
        panel.setMaximumHeight(100)
        panel.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-top: 1px solid #787878;
            }
        """)
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Левая часть — кнопки
        buttons_widget = QWidget()
        buttons_widget.setMaximumWidth(550)
        buttons_layout = QVBoxLayout(buttons_widget)
        buttons_layout.setSpacing(5)
        
        # Кнопки в один ряд
        row1 = QHBoxLayout()
        row1.setSpacing(5)
        
        self.btn_load_vars = QPushButton("📦 Load Variables")
        self.btn_save_workflow = QPushButton("💾 Save Workflow")
        self.btn_export = QPushButton("📤 Export")
        self.btn_import = QPushButton("📥 Import")
        self.btn_compile = QPushButton("⚙️ Compile")
        
        btn_style = """
            QPushButton {
                background-color: #3c3c3c;
                color: #cccccc;
                padding: 5px 10px;
                border: 1px solid #787878;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
                color: #ffffff;
            }
        """
        
        btn_style_primary = """
            QPushButton {
                background-color: #0e639c;
                color: white;
                padding: 5px 10px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """
        
        btn_style_success = """
            QPushButton {
                background-color: #2e7d32;
                color: white;
                padding: 5px 10px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #1b5e20;
            }
        """
        
        self.btn_load_vars.setStyleSheet(btn_style_primary)
        self.btn_save_workflow.setStyleSheet(btn_style_success)
        self.btn_export.setStyleSheet(btn_style)
        self.btn_import.setStyleSheet(btn_style)
        self.btn_compile.setStyleSheet(btn_style)
        
        self.btn_load_vars.clicked.connect(self.load_variables_to_n8n)
        self.btn_save_workflow.clicked.connect(self.save_current_workflow)
        self.btn_export.clicked.connect(self.export_current_workflow)
        self.btn_import.clicked.connect(self.import_workflow_to_n8n)
        self.btn_compile.clicked.connect(self.compile_workflow_to_script)
        
        row1.addWidget(self.btn_load_vars)
        row1.addWidget(self.btn_save_workflow)
        row1.addWidget(self.btn_export)
        row1.addWidget(self.btn_import)
        row1.addWidget(self.btn_compile)
        row1.addStretch()
        
        buttons_layout.addLayout(row1)
        
        # Информация о проекте
        self.project_info = QLabel("📁 No project opened")
        self.project_info.setStyleSheet("color: #787878; font-size: 11px; padding: 2px;")
        buttons_layout.addWidget(self.project_info)
        
        layout.addWidget(buttons_widget)
        
        # Правая часть — консоль
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_layout.setSpacing(2)
        
        self.console_label = QLabel("Console")
        self.console_label.setStyleSheet("color: #0e639c; font-size: 11px;")
        
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setMaximumHeight(60)
        self.console_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
            }
        """)
        
        console_layout.addWidget(self.console_label)
        console_layout.addWidget(self.console_text)
        
        layout.addWidget(console_widget, 1)
        
        return panel
    
    def log(self, message: str):
        """Вывод в консоль"""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.console_text.append(f"[{timestamp}] {message}")
        scrollbar = self.console_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self.log_signal.emit(message)
    
    def on_url_changed(self, url):
        url_str = url.toString()
        if not url_str.startswith("http://localhost:5678"):
            self.n8n_browser.setUrl(QUrl(self.n8n_url))
            self.log("⚠️ Navigation restricted to n8n editor")
        else:
            self.url_label.setText(url_str[:60] + "..." if len(url_str) > 60 else url_str)
    
    def on_load_finished(self, ok):
        if ok and self.current_project:
            QTimer.singleShot(1000, self.inject_project_path_to_n8n)
    
    def create_new_workflow(self):
        self.n8n_browser.setUrl(QUrl(f"{self.n8n_url}/workflows/new"))
        self.log("🆕 Creating new workflow")
    
    def check_n8n_status(self):
        """Проверяет доступность n8n"""
        def check():
            try:
                response = requests.get(f"{self.n8n_url}/healthz", timeout=2)
                if response.status_code == 200:
                    self.n8n_status = True
                    self.log("✅ n8n connected")
                    if self.current_project:
                        QTimer.singleShot(1000, self.inject_project_path_to_n8n)
                else:
                    self.n8n_status = False
            except:
                self.n8n_status = False
                self.log("⚠️ n8n not running. Start with: n8n start --tunnel")
            
            QTimer.singleShot(5000, check)
        
        check()
    
    def inject_project_path_to_n8n(self):
        """Инжектит путь к проекту в n8n"""
        if not self.project_manager or not self.project_manager.current_project:
            return
        
        project_path = os.path.join(self.project_manager.projects_dir, self.project_manager.current_project)
        project_path_normalized = project_path.replace('\\', '/')
        
        # Экранируем путь для JS
        js = f"""
        (function() {{
            localStorage.setItem('upb_project_path', '{project_path_normalized}');
            console.log('UPB: Project path set to', '{project_path_normalized}');
            window.upbProjectPath = '{project_path_normalized}';
            window.dispatchEvent(new CustomEvent('upb_project_loaded', {{
                detail: {{ projectPath: '{project_path_normalized}' }}
            }}));
        }})();
        """
        self.n8n_browser.page().runJavaScript(js)
        self.log(f"📁 Project path injected: {project_path_normalized}")
    
    def save_current_workflow(self):
        """Сохраняет текущий workflow в проект как JSON"""
        if not self.project_manager or not self.project_manager.current_project:
            QMessageBox.warning(self, "No Project", "Open a project first!")
            return
        
        try:
            response = requests.get(f"{self.n8n_url}/api/v1/workflows", timeout=5)
            if response.status_code != 200:
                self.log("❌ Cannot connect to n8n")
                QMessageBox.warning(self, "Error", "n8n is not running!")
                return
            
            workflows = response.json().get('data', [])
            if not workflows:
                QMessageBox.warning(self, "No Workflow", "Create a workflow first!")
                return
            
            if len(workflows) == 1:
                workflow = workflows[0]
            else:
                items = [f"{wf['name']} (ID: {wf['id']})" for wf in workflows]
                selected, ok = QInputDialog.getItem(self, "Save Workflow", "Choose workflow to save:", items, 0, False)
                if not ok:
                    return
                idx = items.index(selected)
                workflow = workflows[idx]
            
            wf_response = requests.get(f"{self.n8n_url}/api/v1/workflows/{workflow['id']}")
            workflow_data = wf_response.json()
            
            workflow_data['upb_metadata'] = {
                'saved_at': datetime.now().isoformat(),
                'project': self.project_manager.current_project,
                'version': '1.0'
            }
            
            project_path = os.path.join(self.project_manager.projects_dir, self.project_manager.current_project)
            workflows_dir = os.path.join(project_path, "workflows")
            os.makedirs(workflows_dir, exist_ok=True)
            
            safe_name = "".join(c for c in workflow['name'] if c.isalnum() or c in ' ._-')
            workflow_file = os.path.join(workflows_dir, f"{safe_name}.json")
            
            with open(workflow_file, 'w', encoding='utf-8') as f:
                json.dump(workflow_data, f, indent=2, ensure_ascii=False)
            
            self.log(f"✅ Workflow saved: {workflow['name']}")
            self.log(f"   📁 Location: {workflow_file}")
            QMessageBox.information(self, "Success", f"Workflow saved to:\n{workflow_file}")
            
        except Exception as e:
            self.log(f"❌ Save error: {e}")
            QMessageBox.warning(self, "Error", str(e))
    
    def load_variables_to_n8n(self):
        """Загружает переменные из variables.xlsx текущего проекта"""
        if not self.project_manager or not self.project_manager.current_project:
            QMessageBox.warning(self, "No Project", "Open a project first!")
            return
        
        project_path = os.path.join(self.project_manager.projects_dir, self.project_manager.current_project)
        variables_file = os.path.join(project_path, "variables.xlsx")
        
        self.log(f"📂 Looking for variables.xlsx in: {variables_file}")
        
        if not os.path.exists(variables_file):
            self.log(f"❌ variables.xlsx not found")
            QMessageBox.warning(self, "Error", f"variables.xlsx not found!\n\nPlease add variables in VM table and save project.")
            return
        
        try:
            import pandas as pd
            df = pd.read_excel(variables_file)
            
            variables = []
            for _, row in df.iterrows():
                var = {
                    'name': row.get('Name', ''),
                    'selector': row.get('XPath/CSS', ''),
                    'type': row.get('Type', 'Static'),
                    'url': row.get('URL', ''),
                    'sample': row.get('Sample Text', '')
                }
                if var['name']:
                    variables.append(var)
            
            if not variables:
                self.log("⚠️ No variables found in variables.xlsx")
                return
            
            var_list = '\n'.join([f"• {v.get('name')} → {v.get('selector', '')[:40]}" for v in variables[:10]])
            self.log(f"✅ Loaded {len(variables)} variables from variables.xlsx:\n{var_list}")
            
            # Сохраняем в JSON для n8n
            vars_json = {}
            for v in variables:
                vars_json[v['name']] = {
                    'selector': v.get('selector', ''),
                    'url': v.get('url', ''),
                    'type': v.get('type', 'text')
                }
            
            # Инжектим в n8n
            vars_json_str = json.dumps(vars_json)
            js = f"""
            (function() {{
                window.upbVariables = {vars_json_str};
                localStorage.setItem('upb_variables', '{vars_json_str}');
                localStorage.setItem('upb_variables_count', '{len(variables)}');
                console.log('UPB: Loaded {len(variables)} variables');
                window.dispatchEvent(new CustomEvent('upb_variables_loaded', {{
                    detail: {{ variables: {vars_json_str} }}
                }}));
            }})();
            """
            self.n8n_browser.page().runJavaScript(js)
            
            QMessageBox.information(self, "Variables Loaded", 
                f"Loaded {len(variables)} variables from variables.xlsx\n\n"
                f"Project: {project_path}\n\n"
                f"Variables:\n{var_list[:500]}")
            
        except ImportError:
            self.log("❌ pandas not installed. Run: pip install pandas openpyxl")
            QMessageBox.warning(self, "Error", "pandas not installed!\n\nRun: pip install pandas openpyxl")
        except Exception as e:
            self.log(f"❌ Error loading variables: {e}")
            QMessageBox.warning(self, "Error", str(e))

    def export_current_workflow(self):
        """Экспорт текущего workflow из n8n в проект UPB (копия)"""
        if not self.project_manager or not self.project_manager.current_project:
            QMessageBox.warning(self, "No Project", "Open a project first!")
            return
        
        try:
            response = requests.get(f"{self.n8n_url}/api/v1/workflows", timeout=5)
            if response.status_code != 200:
                self.log("❌ Cannot connect to n8n")
                QMessageBox.warning(self, "Error", "n8n is not running!")
                return
            
            workflows = response.json().get('data', [])
            if not workflows:
                QMessageBox.information(self, "No Workflows", "Create a workflow in n8n first!")
                return
            
            if len(workflows) == 1:
                workflow = workflows[0]
            else:
                items = [f"{wf['name']} (ID: {wf['id']})" for wf in workflows]
                selected, ok = QInputDialog.getItem(self, "Export Workflow", "Choose workflow:", items, 0, False)
                if not ok:
                    return
                idx = items.index(selected)
                workflow = workflows[idx]
            
            wf_response = requests.get(f"{self.n8n_url}/api/v1/workflows/{workflow['id']}")
            workflow_data = wf_response.json()
            
            project_path = os.path.join(self.project_manager.projects_dir, self.project_manager.current_project)
            workflows_dir = os.path.join(project_path, "workflows")
            os.makedirs(workflows_dir, exist_ok=True)
            
            safe_name = "".join(c for c in workflow['name'] if c.isalnum() or c in ' ._-')
            workflow_file = os.path.join(workflows_dir, f"{safe_name}_export.json")
            
            with open(workflow_file, 'w', encoding='utf-8') as f:
                json.dump(workflow_data, f, indent=2, ensure_ascii=False)
            
            self.log(f"✅ Exported: {workflow['name']}")
            QMessageBox.information(self, "Success", f"Exported to:\n{workflow_file}")
            
        except Exception as e:
            self.log(f"❌ Export error: {e}")
    
    def import_workflow_to_n8n(self):
        """Импорт workflow из проекта UPB в n8n"""
        if not self.project_manager or not self.project_manager.current_project:
            QMessageBox.warning(self, "No Project", "Open a project first!")
            return
        
        project_path = os.path.join(self.project_manager.projects_dir, self.project_manager.current_project)
        workflows_dir = os.path.join(project_path, "workflows")
        
        if not os.path.exists(workflows_dir):
            QMessageBox.information(self, "No Workflows", "No workflows found in project")
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Workflow", workflows_dir, "JSON Files (*.json)"
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                workflow_data = json.load(f)
            
            response = requests.post(
                f"{self.n8n_url}/api/v1/workflows/import",
                json=workflow_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                self.log("✅ Imported successfully")
                QMessageBox.information(self, "Success", "Workflow imported!\nRefresh page to see it.")
                self.n8n_browser.reload()
            else:
                self.log(f"❌ Import failed: {response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Import error: {e}")
    
    def compile_workflow_to_script(self):
        """Компиляция workflow в script.txt"""
        if not self.project_manager or not self.project_manager.current_project:
            QMessageBox.warning(self, "No Project", "Open a project first!")
            return
        
        try:
            response = requests.get(f"{self.n8n_url}/api/v1/workflows", timeout=5)
            if response.status_code != 200:
                self.log("❌ Cannot connect to n8n")
                QMessageBox.warning(self, "Error", "n8n is not running!")
                return
            
            workflows = response.json().get('data', [])
            if not workflows:
                QMessageBox.warning(self, "No Workflow", "Create a workflow first!")
                return
            
            if len(workflows) == 1:
                workflow = workflows[0]
            else:
                items = [f"{wf['name']} (ID: {wf['id']})" for wf in workflows]
                selected, ok = QInputDialog.getItem(self, "Compile Workflow", "Choose workflow to compile:", items, 0, False)
                if not ok:
                    return
                idx = items.index(selected)
                workflow = workflows[idx]
            
            wf_response = requests.get(f"{self.n8n_url}/api/v1/workflows/{workflow['id']}")
            workflow_data = wf_response.json()
            
            script_lines = self._workflow_to_script(workflow_data)
            
            project_path = os.path.join(self.project_manager.projects_dir, self.project_manager.current_project)
            script_path = os.path.join(project_path, "script.txt")
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(script_lines))
            
            self.log(f"✅ Compiled '{workflow['name']}' to script.txt")
            self.log(f"   📁 Location: {script_path}")
            commands_count = len([l for l in script_lines if l and not l.startswith('#')])
            self.log(f"   📊 Commands: {commands_count}")
            
            QMessageBox.information(self, "Success", 
                f"Workflow compiled to script.txt!\n\n"
                f"Location: {script_path}\n"
                f"Commands: {commands_count}")
            
        except Exception as e:
            self.log(f"❌ Compilation error: {e}")
            QMessageBox.warning(self, "Error", str(e))
    
    def _workflow_to_script(self, workflow_data):
        """Конвертирует workflow в команды script.txt"""
        lines = []
        lines.append(f"# Workflow: {workflow_data.get('name', 'untitled')}")
        lines.append(f"# ID: {workflow_data.get('id', 'unknown')}")
        lines.append(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        lines.append("# ============================================")
        lines.append("# UPB Parser Script")
        lines.append("# ============================================")
        lines.append("")
        
        nodes = workflow_data.get('nodes', [])
        nodes_sorted = sorted(nodes, key=lambda n: n.get('position', [0, 0])[1])
        
        for node in nodes_sorted:
            node_type = node.get('type', '')
            node_name = node.get('name', 'unknown')
            params = node.get('parameters', {})
            
            lines.append(f"# Node: {node_name}")
            
            if node_type == 'n8n-nodes-base.upbParser':
                operation = params.get('operation', '')
                if operation == 'loadVariables':
                    lines.append("# Variables loaded from project")
                    lines.append("")
                    continue
                elif operation == 'extractText':
                    selector = params.get('selector', '')
                    save_to = params.get('saveTo', 'result')
                    lines.append(f"extract_text {selector} -> {save_to}")
                elif operation == 'extractAttribute':
                    selector = params.get('selector', '')
                    attribute = params.get('attributeName', 'href')
                    save_to = params.get('saveTo', 'result')
                    lines.append(f"extract_attribute {selector} {attribute} -> {save_to}")
                elif operation == 'extractHtml':
                    selector = params.get('selector', '')
                    save_to = params.get('saveTo', 'result')
                    lines.append(f"extract_html {selector} -> {save_to}")
                elif operation == 'extractList':
                    container = params.get('containerSelector', '')
                    save_to = params.get('saveTo', 'result')
                    lines.append(f"extract_list {container} -> {save_to}")
                elif operation == 'click':
                    lines.append(f"click {params.get('selector', '')}")
                elif operation == 'type':
                    text = params.get('text', '')
                    lines.append(f"type {params.get('selector', '')} \"{text}\"")
                elif operation == 'wait':
                    lines.append(f"wait {params.get('seconds', 1)}")
                elif operation == 'openUrl':
                    lines.append(f"open_url {params.get('url', '')}")
                elif operation == 'screenshot':
                    lines.append(f"screenshot {params.get('filename', 'screenshot.png')}")
                elif operation == 'saveExcel':
                    lines.append(f"save_excel {params.get('data', '')} -> {params.get('filename', 'output.xlsx')}")
                elif operation == 'saveJson':
                    lines.append(f"save_json {params.get('data', '')} -> {params.get('filename', 'output.json')}")
                elif operation == 'createVariable':
                    lines.append(f"create_var {params.get('varName', '')} = {params.get('varValue', '')}")
                elif operation == 'updateVariable':
                    lines.append(f"update_var {params.get('varName', '')} = {params.get('varValue', '')}")
                elif operation == 'createList':
                    lines.append(f"create_list {params.get('varName', '')}")
                elif operation == 'appendToList':
                    lines.append(f"append_list {params.get('listName', '')} {params.get('varValue', '')}")
                elif operation == 'print':
                    lines.append(f"print {params.get('printValue', '')}")
                elif operation == 'log':
                    msg = params.get('message', '')
                    level = params.get('logLevel', 'info')
                    lines.append(f"log {msg} level={level}")
                else:
                    lines.append(f"# Unknown operation: {operation}")
            
            elif node_type == 'n8n-nodes-base.httpRequest':
                url = params.get('url', '')
                method = params.get('method', 'GET')
                lines.append(f"http_{method.lower()} {url}")
            
            elif node_type == 'n8n-nodes-base.manualTrigger':
                lines.append("# Manual trigger - run on demand")
                continue
            
            elif node_type == 'n8n-nodes-base.scheduleTrigger':
                lines.append("# Schedule trigger - runs automatically")
                continue
            
            elif node_type == 'n8n-nodes-base.webhook':
                path = params.get('path', '')
                lines.append(f"# Webhook trigger at: /webhook/{path}")
                continue
            
            else:
                lines.append(f"# Unsupported node type: {node_type}")
                continue
            
            lines.append("")
        
        return lines
    
    def update_project(self, project_name):
        """Обновляет текущий проект"""
        self.current_project = project_name
        if project_name:
            project_path = os.path.join(self.project_manager.projects_dir, project_name)
            self.project_info.setText(f"📁 Project: {project_name}")
            self.project_info.setStyleSheet("color: #0e639c; font-size: 11px;")
            self.inject_project_path_to_n8n()
            
            script_path = os.path.join(project_path, "script.txt")
            if os.path.exists(script_path):
                self.log(f"📄 Existing script.txt found in project")
            else:
                self.log(f"📄 No script.txt yet. Create a workflow and compile it!")
        else:
            self.project_info.setText("📁 No project opened")
            self.project_info.setStyleSheet("color: #787878; font-size: 11px;")