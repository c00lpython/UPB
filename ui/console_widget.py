# ui/console_widget.py
from PySide6.QtWidgets import QTextEdit, QWidget, QVBoxLayout
from PySide6.QtCore import QDateTime


class ConsoleWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        # ⚠️ УБИРАЕМ setMaximumHeight(120) — теперь консоль может растягиваться!
        # self.text_edit.setMaximumHeight(120)  # ❌ УДАЛИТЬ!
        
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #cccccc;
                font-family: Consolas, monospace;
                border: 1px solid #3c3c3c;
            }
        """)
        
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
        
        self.log("Console ready")
    
    def log(self, message: str):
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.text_edit.append(f"[{timestamp}] {message}")