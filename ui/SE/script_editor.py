import os
import json
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

from ui.SE.ui.blocks_palette import BlocksPalette
from ui.SE.ui.canvas_widget import CanvasWidget
from ui.SE.ui.properties_editor import PropertiesEditor


class ScriptEditor(QWidget):
    
    log_signal = pyqtSignal(str)
    
    def __init__(self, project_manager=None, parent=None):
        super().__init__(parent)
        self.project_manager = project_manager
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
        self.properties = PropertiesEditor()
        self.properties.property_changed.connect(self.on_property_changed)
        right_layout.addWidget(self.properties)
        main_splitter.addWidget(right_widget)
        
        main_splitter.setSizes([250, 600, 320])
        
        # Нижняя панель
        bottom_bar = QWidget()
        bottom_bar.setFixedHeight(55)
        bottom_bar.setStyleSheet("QWidget { background-color: #2d2d2d; border-top: 1px solid #444; }")
        
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(15, 8, 15, 8)
        bottom_layout.setSpacing(15)
        
        self.btn_compile = QPushButton("⚙️ Compile to Script")
        self.btn_compile.setMinimumWidth(160)
        self.btn_compile.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_compile.setStyleSheet("QPushButton { background-color: #0e639c; color: white; border: none; border-radius: 5px; padding: 8px 16px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #1177bb; }")
        self.btn_compile.clicked.connect(self.compile_workflow)
        
        self.btn_clear = QPushButton("🗑️ Clear Canvas")
        self.btn_clear.setMinimumWidth(120)
        self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_clear.setStyleSheet("QPushButton { background-color: #4a4a4a; color: #ddd; border: none; border-radius: 5px; padding: 8px 16px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #5a5a5a; }")
        self.btn_clear.clicked.connect(self.clear_canvas)
        
        self.btn_save = QPushButton("💾 Save Scheme")
        self.btn_save.setMinimumWidth(130)
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; border: none; border-radius: 5px; padding: 8px 16px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #1b5e20; }")
        self.btn_save.clicked.connect(self.save_workflow)
        
        self.btn_load = QPushButton("📂 Load Scheme")
        self.btn_load.setMinimumWidth(130)
        self.btn_load.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_load.setStyleSheet("QPushButton { background-color: #6c3483; color: white; border: none; border-radius: 5px; padding: 8px 16px; font-weight: bold; font-size: 12px; } QPushButton:hover { background-color: #512e5f; }")
        self.btn_load.clicked.connect(self.load_workflow)
        
        bottom_layout.addWidget(self.btn_compile)
        bottom_layout.addWidget(self.btn_clear)
        bottom_layout.addWidget(self.btn_save)
        bottom_layout.addWidget(self.btn_load)
        
        self.status_label = QLabel("● Ready")
        self.status_label.setStyleSheet("QLabel { color: #2ecc71; font-size: 11px; font-weight: bold; padding: 0 10px; }")
        bottom_layout.addWidget(self.status_label, 1)
        
        self.block_count_label = QLabel("0 blocks")
        self.block_count_label.setStyleSheet("color: #888; font-size: 11px;")
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
    
    def compile_workflow(self):
        nodes = self.canvas.get_all_blocks()
        if not nodes:
            QMessageBox.warning(self, "Empty Workflow", "Add some blocks to the canvas first!")
            self.update_status("Cannot compile: empty workflow", True)
            return
        
        lines = []
        lines.append("# UPB Parser Script")
        lines.append(f"# Generated: {QDateTime.currentDateTime().toString()}")
        lines.append(f"# Total blocks: {len(nodes)}")
        lines.append("")
        
        for i, node in enumerate(nodes, 1):
            block = node.block
            lines.append(f"# [{i}] {block.name} ({block.node_type})")
            cmd = self.block_to_command(block)
            lines.append(cmd)
            lines.append("")
        
        if self.project_manager and self.project_manager.current_project:
            project_path = os.path.join(self.project_manager.projects_dir, self.project_manager.current_project)
            script_path = os.path.join(project_path, "script.txt")
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            self.update_status(f"✅ Compiled to {script_path}")
            QMessageBox.information(self, "Success", f"Workflow compiled!\n\n{script_path}")
        else:
            preview = '\n'.join(lines[:30])
            QMessageBox.information(self, "Preview", f"No project opened.\n\n{preview}")
    
    def block_to_command(self, block) -> str:
        p = block.params
        commands = {
            "startofwork": f"start_session project={p.get('projectName', '')} headless={p.get('headless', True)}",
            "openurl": f"open_url url={p.get('url', '')} wait={p.get('waitStrategy', 'load')}",
            "click": f"click selector={p.get('selector', '')}",
            "type": f"type selector={p.get('selector', '')} text={p.get('text', '')}",
            "parsedata": f"parse_data var={p.get('varName', '')} save_to={p.get('saveTo', 'result')}",
            "screenshot": f"screenshot filename={p.get('filename', 'screenshot.png')}",
            "convertexcel": f"convert_excel input={p.get('inputFile', '')} format={p.get('outputFormat', 'csv')}",
            "forloop": f"for iterator={p.get('iterator', 'item')} in {p.get('iterable', '')}",
            "if": f"if {p.get('left', '')} {p.get('operator', 'eq')} {p.get('right', '')}",
            "end": f"end",
            "reload": f"reload wait={p.get('waitAfter', 2000)}",
            "sendtelegram": f"send_telegram token={p.get('botToken', '')} chat={p.get('chatId', '')} msg={p.get('message', '')}",
            "savedata": f"save_data var={p.get('dataVar', '')} format={p.get('format', 'excel')}",
            "endsession": f"end_session save={p.get('saveResults', True)} close={p.get('closeBrowser', True)}"
        }
        return commands.get(block.node_type, f"# TODO: implement {block.node_type}")
    
    def clear_canvas(self):
        if len(self.canvas.get_all_blocks()) > 0:
            reply = QMessageBox.question(self, "Clear Canvas", "Clear all blocks?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.canvas.clear()
                self.properties.set_block(None)
                self.update_status("Canvas cleared")
    
    def save_workflow(self):
        if not self.project_manager or not self.project_manager.current_project:
            QMessageBox.warning(self, "No Project", "Open a project first!")
            return
        
        nodes = self.canvas.get_all_blocks()
        project_path = os.path.join(self.project_manager.projects_dir, self.project_manager.current_project)
        scheme_path = os.path.join(project_path, "workflow.workscheme")
        
        data = {"version": "1.0", "created": QDateTime.currentDateTime().toString(), "blocks": []}
        for node in nodes:
            block = node.block
            data["blocks"].append({
                "id": block.id,
                "type": block.node_type,
                "name": block.name,
                "x": block.position["x"],
                "y": block.position["y"],
                "color": block.color,
                "params": block.params
            })
        
        with open(scheme_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self.update_status(f"Saved to {scheme_path}")
        QMessageBox.information(self, "Success", f"Scheme saved!\n\n{scheme_path}")
    
    def load_workflow(self):
        if not self.project_manager or not self.project_manager.current_project:
            QMessageBox.warning(self, "No Project", "Open a project first!")
            return
        
        project_path = os.path.join(self.project_manager.projects_dir, self.project_manager.current_project)
        scheme_path = os.path.join(project_path, "workflow.workscheme")
        
        if not os.path.exists(scheme_path):
            QMessageBox.warning(self, "Not Found", f"No workflow.workscheme found")
            return
        
        try:
            with open(scheme_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.canvas.clear()
            for block_data in data.get("blocks", []):
                self.canvas.add_block_from_data(
                    block_data["type"],
                    block_data["name"],
                    block_data["x"],
                    block_data["y"],
                    block_data.get("color", "#3498db")
                )
            self.update_status(f"Loaded {len(data.get('blocks', []))} blocks")
        except Exception as e:
            self.update_status(f"Error loading: {e}", True)