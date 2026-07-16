# ui/SE/script_editor.py

import os
import json
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

from ui.SE.ui.blocks_palette import BlocksPalette
from ui.SE.ui.canvas_widget import CanvasWidget
from ui.SE.ui.properties_editor import PropertiesEditor
from ui.SE.core.serialization import upb_serializer
from ui.SE.core.compiler import UPBCompiler, compile_workflow
from ui.animated_button import GradientFollowButton, AnimatedButton


class ScriptEditor(QWidget):
    
    log_signal = Signal(str)
    
    def __init__(self, project_manager=None, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.current_project = None
        self.current_workflow_file = None
        self.variables = {}
        self.variables_path = None
        
        self.init_ui()
    
    def init_ui(self):
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setHandleWidth(2)
        main_splitter.setStyleSheet("QSplitter::handle { background-color: #444; width: 2px; }")
        
        # Левая панель - палитра
        left_widget = QWidget()
        left_widget.setMaximumWidth(280)
        left_widget.setMinimumWidth(220)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        self.palette = BlocksPalette()
        left_layout.addWidget(self.palette)
        main_splitter.addWidget(left_widget)
        
        # Центральная панель - канвас
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setContentsMargins(0, 0, 0, 0)
        self.canvas = CanvasWidget()
        self.canvas.block_selected.connect(self.on_block_selected)
        center_layout.addWidget(self.canvas)
        main_splitter.addWidget(center_widget)
        
        # Правая панель - свойства
        right_widget = QWidget()
        right_widget.setMaximumWidth(350)
        right_widget.setMinimumWidth(280)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        self.properties = PropertiesEditor(get_variables_callback=self.get_variables)
        self.properties.property_changed.connect(self.on_property_changed)
        right_layout.addWidget(self.properties)
        main_splitter.addWidget(right_widget)
        
        main_splitter.setSizes([250, 600, 320])
        
        # ========== НИЖНЯЯ ПАНЕЛЬ ==========
        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(55)
        bottom_bar.setStyleSheet("""
            QWidget { 
                background-color: #2d2d2d; 
                border-top: 1px solid #444; 
            }
        """)
        
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(15, 8, 15, 8)
        bottom_layout.setSpacing(15)
        
        self.btn_compile = GradientFollowButton("⚙️ Compile to Script")
        self.btn_compile.setProperty("type", "primary")
        self.btn_compile.setMinimumWidth(160)
        self.btn_compile.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_compile.setFixedHeight(38)
        self.btn_compile.clicked.connect(self.compile_workflow)

        self.btn_clear = GradientFollowButton("🗑️ Clear Canvas")
        self.btn_clear.setProperty("type", "danger")
        self.btn_clear.setMinimumWidth(120)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setFixedHeight(38)
        self.btn_clear.clicked.connect(self.clear_canvas)

        self.btn_save = GradientFollowButton("💾 Save Workflow")
        self.btn_save.setProperty("type", "primary")
        self.btn_save.setMinimumWidth(140)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setFixedHeight(38)
        self.btn_save.clicked.connect(self.save_workflow)

        self.btn_load = GradientFollowButton("📂 Load Workflow")
        self.btn_load.setProperty("type", "default")
        self.btn_load.setMinimumWidth(140)
        self.btn_load.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_load.setFixedHeight(38)
        self.btn_load.clicked.connect(self.load_workflow)

        self.btn_new = GradientFollowButton("✨ New Workflow")
        self.btn_new.setProperty("type", "primary")
        self.btn_new.setMinimumWidth(140)
        self.btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new.setFixedHeight(38)
        self.btn_new.clicked.connect(self.new_workflow)
        
        bottom_layout.addWidget(self.btn_compile)
        bottom_layout.addWidget(self.btn_clear)
        bottom_layout.addWidget(self.btn_save)
        bottom_layout.addWidget(self.btn_load)
        bottom_layout.addWidget(self.btn_new)
        
        self.status_label = QLabel("● Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #2ecc71;
                font-size: 11px;
                font-weight: bold;
                padding: 0 10px;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
        """)
        bottom_layout.addWidget(self.status_label, 1)
        
        self.block_count_label = QLabel("0 blocks")
        self.block_count_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 11px;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
        """)
        bottom_layout.addWidget(self.block_count_label)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(main_splitter)
        main_layout.addWidget(bottom_bar)
        
        # Устанавливаем связь канваса с родителем
        self.canvas.parent_window = self
    
    def log(self, message: str):
        self.log_signal.emit(message)
    
    def on_block_selected(self, node):
        if node and hasattr(node, 'block'):
            self.properties.set_block(node.block)
            self.update_status(f"Selected: {node.block.name}")
    
    def on_property_changed(self, block_id, prop_name, value):
        self.update_status(f"Updated {prop_name} = {str(value)[:40]}")
        if self.project_manager and self.project_manager.current_project:
            self.auto_save_workflow()
    
    def update_status(self, message, is_error=False):
        self.log(message)
        self.status_label.setText(f"● {message}")
        if is_error:
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 11px; font-weight: bold;")
            QTimer.singleShot(3000, lambda: self.status_label.setStyleSheet("color: #2ecc71; font-size: 11px; font-weight: bold;"))
        else:
            self.status_label.setStyleSheet("color: #2ecc71; font-size: 11px; font-weight: bold;")
        
        block_count = len(self.canvas.get_all_blocks())
        self.block_count_label.setText(f"{block_count} blocks")
    
    # ========================================================================
    # Управление переменными
    # ========================================================================
    
    def get_variables(self) -> dict:
        print(f"🔙 [CALLBACK] get_variables called, returning {len(self.variables)} vars: {list(self.variables.keys())[:5]}")
        return self.variables
    
    def load_variables_from_project(self, project_name: str):
        """Загружает переменные из variables.xlsx текущего проекта"""
        if not self.project_manager:
            self.variables = {}
            self.variables_path = None
            return
        
        project_path = os.path.join(self.project_manager.projects_dir, project_name)
        variables_file = os.path.join(project_path, "variables.xlsx")
        self.variables_path = variables_file if os.path.exists(variables_file) else None
        
        if os.path.exists(variables_file):
            try:
                import pandas as pd
                df = pd.read_excel(variables_file)
                self.variables = {}
                
                for _, row in df.iterrows():
                    name = row.get('Name')
                    if name and not pd.isna(name):
                        name_str = str(name).strip()
                        self.variables[name_str] = {
                            'selector': str(row.get('XPath/CSS', '')) if not pd.isna(row.get('XPath/CSS', '')) else '',
                            'url': str(row.get('URL', '')) if not pd.isna(row.get('URL', '')) else '',
                            'type': str(row.get('Type', 'Static')) if not pd.isna(row.get('Type', 'Static')) else 'Static',
                            'sample': str(row.get('Sample Text', '')) if not pd.isna(row.get('Sample Text', '')) else ''
                        }
                
                self.update_status(f"📦 Loaded {len(self.variables)} variables from variables.xlsx")
                print(f"✅ Загружено {len(self.variables)} переменных из {variables_file}")
                
                if self.properties.current_block:
                    self.properties.refresh()
                    
            except ImportError:
                self.update_status("⚠️ pandas not installed. Run: pip install pandas openpyxl", True)
                print("⚠️ pandas not installed. Run: pip install pandas openpyxl")
                self.variables = {}
                self.variables_path = None
            except Exception as e:
                self.update_status(f"⚠️ Error loading variables: {e}", True)
                print(f"⚠️ Ошибка загрузки переменных: {e}")
                self.variables = {}
                self.variables_path = None
        else:
            self.variables = {}
            self.variables_path = None
            print(f"⚠️ Файл variables.xlsx не найден в {project_path}")
    
    # ========================================================================
    # Компиляция (с использованием UPBCompiler)
    # ========================================================================
    
    def compile_workflow(self):
        nodes = self.canvas.get_all_blocks()
        if not nodes:
            QMessageBox.warning(self, "Empty Workflow", "Add some blocks to the canvas first!")
            self.update_status("Cannot compile: empty workflow", True)
            return
        
        if not self.project_manager or not self.project_manager.current_project:
            QMessageBox.warning(self, "No Project", "Open a project first!")
            return
        
        project_path = os.path.join(self.project_manager.projects_dir, self.project_manager.current_project)
        workflow_file = os.path.join(project_path, "workflow.json")
        
        # Сохраняем workflow
        upb_serializer.save_project(self.canvas, workflow_file)
        
        # Компилируем в script.txt
        script_path = os.path.join(project_path, "script.txt")
        
        try:
            compiler = UPBCompiler(workflow_file, self.variables_path)
            script = compiler.compile(mode="chain")
            compiler.save(script_path, mode="chain")
            
            self.update_status(f"✅ Compiled to {script_path}")
            QMessageBox.information(self, "Success", f"Workflow compiled!\n\n{script_path}")
        except Exception as e:
            self.update_status(f"❌ Compilation error: {str(e)}", True)
            QMessageBox.critical(self, "Error", f"Compilation failed:\n\n{str(e)}")
            import traceback
            traceback.print_exc()

    def block_to_command(self, block) -> str:
        p = block.params
        commands = {
            "startofwork": f"start_session project={p.get('projectName', '')} headless={p.get('headless', True)} timeout={p.get('timeout', 30)}",
            "openurl": f"open_url url={p.get('url', '')} wait={p.get('waitStrategy', 'load')} timeout={p.get('timeout', 30000)}",
            "click": f"click selector={p.get('selector', '')} type={p.get('selectorType', 'css')} count={p.get('clickCount', 1)} wait={p.get('waitAfter', 1000)}",
            "type": f"type selector={p.get('selector', '')} type={p.get('selectorType', 'css')} text='{p.get('text', '')}' clear={p.get('clearFirst', True)} enter={p.get('pressEnter', False)} delay={p.get('delay', 0)}",
            "parsedata": f"parse_data var={p.get('varName', '')} save_to={p.get('saveTo', 'result')} extract={p.get('extractType', 'text')} attribute={p.get('attributeName', '')}",
            "screenshot": f"screenshot filename={p.get('filename', 'screenshot.png')} full={p.get('fullPage', False)} selector={p.get('selector', '')}",
            "convertexcel": f"convert_excel input={p.get('inputFile', '')} format={p.get('outputFormat', 'csv')} output={p.get('outputFile', '')} sheet={p.get('sheetName', 'Sheet1')}",
            "forloop": f"for iterator={p.get('iterator', 'item')} type={p.get('iterableType', 'variable')} in {p.get('iterable', '')}",
            "if": f"if {p.get('left', '')} {p.get('operator', 'eq')} {p.get('right', '')}",
            "end": f"end type={p.get('blockType', 'loop')}",
            "reload": f"reload wait={p.get('waitAfter', 2000)} nocache={p.get('ignoreCache', True)}",
            "sendtelegram": f"send_telegram token={p.get('botToken', '')} chat={p.get('chatId', '')} msg='{p.get('message', '')}' parse={p.get('parseMode', '')}",
            "savedata": f"save_data var={p.get('dataVar', '')} format={p.get('format', 'excel')} path={p.get('outputPath', './output')} overwrite={p.get('overwrite', True)}",
            "endsession": f"end_session save={p.get('saveResults', True)} close={p.get('closeBrowser', True)} report={p.get('exportReport', False)}"
        }
        return commands.get(block.node_type, f"# TODO: implement {block.node_type}")
    
    # ========================================================================
    # Управление канвасом
    # ========================================================================
    
    def clear_canvas(self):
        if len(self.canvas.get_all_blocks()) > 0:
            reply = QMessageBox.question(self, "Clear Canvas", "Clear all blocks?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.canvas.clear()
                self.properties.set_block(None)
                self.update_status("Canvas cleared")
    
    def save_workflow(self):
        """Сохраняет workflow через сериализатор"""
        if not self.project_manager or not self.project_manager.current_project:
            QMessageBox.warning(self, "No Project", "Open a project first!")
            return
        
        project_path = os.path.join(self.project_manager.projects_dir, self.project_manager.current_project)
        workflow_file = os.path.join(project_path, "workflow.json")
        
        success = upb_serializer.save_project(self.canvas, workflow_file)
        
        if success:
            self.current_workflow_file = workflow_file
            self.update_status(f"✅ Workflow saved to {workflow_file}")
            QMessageBox.information(self, "Success", f"Workflow saved!\n\n{workflow_file}")
        else:
            self.update_status("❌ Failed to save workflow", True)
            QMessageBox.warning(self, "Error", "Failed to save workflow!")
    
    def load_workflow(self):
        """Загружает workflow через сериализатор"""
        if not self.project_manager or not self.project_manager.current_project:
            QMessageBox.warning(self, "No Project", "Open a project first!")
            return
        
        project_path = os.path.join(self.project_manager.projects_dir, self.project_manager.current_project)
        workflow_file = os.path.join(project_path, "workflow.json")
        
        if not os.path.exists(workflow_file):
            QMessageBox.warning(self, "Not Found", f"No workflow.json found in project folder!")
            return
        
        if len(self.canvas.get_all_blocks()) > 0:
            reply = QMessageBox.question(self, "Load Workflow", 
                                         "Current workflow will be lost. Continue?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        success = upb_serializer.load_project(workflow_file, self.canvas)
        
        if success:
            # ПРИНУДИТЕЛЬНО ОБНОВЛЯЕМ ВСЕ СОЕДИНЕНИЯ ПОСЛЕ ЗАГРУЗКИ
            self.canvas.update_all_connections()
            
            self.current_workflow_file = workflow_file
            self.update_status(f"✅ Workflow loaded from {workflow_file}")
            QMessageBox.information(self, "Success", f"Workflow loaded!\n\nBlocks: {len(self.canvas.get_all_blocks())}")
        else:
            self.update_status("❌ Failed to load workflow", True)
            QMessageBox.warning(self, "Error", "Failed to load workflow!")
    
    def new_workflow(self):
        """Создаёт новый workflow"""
        if len(self.canvas.get_all_blocks()) > 0:
            reply = QMessageBox.question(self, "New Workflow", 
                                         "Current workflow will be lost. Create new?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.canvas.clear()
        self.properties.set_block(None)
        self.current_workflow_file = None
        self.update_status("✨ New workflow created")
    
    def auto_save_workflow(self):
        """Автоматическое сохранение при изменениях"""
        if self.project_manager and self.project_manager.current_project:
            project_path = os.path.join(self.project_manager.projects_dir, self.project_manager.current_project)
            workflow_file = os.path.join(project_path, "workflow.json")
            upb_serializer.save_project(self.canvas, workflow_file)
    
    # ========================================================================
    # Управление проектом
    # ========================================================================
    
    def update_project(self, project_name: str):
        """
        Обновляет проект при переключении между проектами
        Вызывается из main_window при открытии/создании проекта
        """
        # Сохраняем текущий workflow в старый проект если был открыт
        if self.current_project and self.project_manager:
            old_project_path = os.path.join(self.project_manager.projects_dir, self.current_project)
            old_workflow_file = os.path.join(old_project_path, "workflow.json")
            upb_serializer.save_project(self.canvas, old_workflow_file)
            self.update_status(f"💾 Saved workflow to: {self.current_project}")
        
        # Обновляем текущий проект
        self.current_project = project_name
        
        if project_name and self.project_manager:
            # Загружаем переменные из variables.xlsx
            self.load_variables_from_project(project_name)
            
            project_path = os.path.join(self.project_manager.projects_dir, project_name)
            workflow_file = os.path.join(project_path, "workflow.json")
            
            # Очищаем канвас перед загрузкой
            self.canvas.clear()
            self.properties.set_block(None)
            
            if os.path.exists(workflow_file):
                # Загружаем сохранённый workflow
                success = upb_serializer.load_project(workflow_file, self.canvas)
                if success:
                    # ПРИНУДИТЕЛЬНО ОБНОВЛЯЕМ ВСЕ СОЕДИНЕНИЯ ПОСЛЕ ЗАГРУЗКИ
                    self.canvas.update_all_connections()
                    
                    self.update_status(f"📁 Loaded workflow for: {project_name}")
                    block_count = len(self.canvas.get_all_blocks())
                    self.block_count_label.setText(f"{block_count} blocks")
                else:
                    self.update_status(f"⚠️ Could not load workflow for: {project_name}", True)
                    self.block_count_label.setText("0 blocks")
            else:
                # Новый проект - пустой канвас
                self.update_status(f"📁 New project: {project_name} (no workflow yet)")
                self.block_count_label.setText("0 blocks")
            
            # Обновляем заголовок окна
            if self.parent() and hasattr(self.parent(), 'setWindowTitle'):
                self.parent().setWindowTitle(f"UPB - {project_name}")
    
    def closeEvent(self, event):
        """При закрытии редактора сохраняем текущий workflow"""
        if self.current_project and self.project_manager:
            project_path = os.path.join(self.project_manager.projects_dir, self.current_project)
            workflow_file = os.path.join(project_path, "workflow.json")
            upb_serializer.save_project(self.canvas, workflow_file)
            self.update_status(f"💾 Auto-saved workflow for: {self.current_project}")
        super().closeEvent(event)