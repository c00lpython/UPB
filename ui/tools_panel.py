from PySide6.QtWidgets import QVBoxLayout, QPushButton, QFrame
from PySide6.QtCore import Signal


class ToolsPanel(QFrame):
    select_clicked = Signal()
    build_clicked = Signal()
    run_clicked = Signal()
    
    def __init__(self):
        super().__init__()
        self.setMaximumWidth(120)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Кнопка Select
        self.btn_select = QPushButton("Select")
        self.btn_select.setCheckable(True)
        self.btn_select.clicked.connect(self.on_select_clicked)
        self.btn_select.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: white;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #007acc;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
        """)
        
        # Кнопка Build
        self.btn_build = QPushButton("Build")
        self.btn_build.clicked.connect(self.build_clicked.emit)
        
        # Кнопка Run
        self.btn_run = QPushButton("Run")
        self.btn_run.clicked.connect(self.run_clicked.emit)
        
        layout.addWidget(self.btn_select)
        layout.addWidget(self.btn_build)
        layout.addWidget(self.btn_run)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def on_select_clicked(self):
        self.select_clicked.emit()