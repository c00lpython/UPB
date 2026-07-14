# ui/SE/ui/blocks_palette.py - полная версия с маркерами

import json
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


class BlocksPalette(QWidget):
    
    def __init__(self):
        print("🏁 [PALETTE] __init__ START")
        super().__init__()
        self.setup_ui()
        self.create_blocks()
        print("🏁 [PALETTE] __init__ END")
    
    def setup_ui(self):
        print("🔧 [PALETTE] setup_ui START")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        header = QLabel("📦 UPB NODES")
        header.setFixedHeight(40)
        header.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                color: #3d5afe;
                font-weight: bold;
                font-size: 12px;
                padding-left: 15px;
                border-bottom: 1px solid #444;
            }
        """)
        layout.addWidget(header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #252525;
            }
            QScrollBar:vertical {
                background: #252525;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #444;
                border-radius: 5px;
            }
        """)
        
        self.container = QWidget()
        self.container.setStyleSheet("background: #252525;")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(10, 10, 10, 10)
        self.container_layout.setSpacing(8)
        self.container_layout.addStretch()
        
        scroll.setWidget(self.container)
        layout.addWidget(scroll)
        print("🔧 [PALETTE] setup_ui END")
    
    def create_blocks(self):
        print("📦 [PALETTE] create_blocks START")
        blocks = [
            ("🚀", "Start of Work", "startofwork", "#2ecc71"),
            ("🌐", "Open URL", "openurl", "#3498db"),
            ("🖱️", "Click", "click", "#e67e22"),
            ("⌨️", "Type", "type", "#9b59b6"),
            ("📊", "Parse Data", "parsedata", "#1abc9c"),
            ("📸", "Screenshot", "screenshot", "#f39c12"),
            ("📑", "Convert Excel", "convertexcel", "#95a5a6"),
            ("🔄", "For Loop", "forloop", "#e74c3c"),
            ("⚡", "If Condition", "if", "#e74c3c"),
            ("⏹️", "End Block", "end", "#7f8c8d"),
            ("🔄", "Reload", "reload", "#f39c12"),
            ("📨", "Send Telegram", "sendtelegram", "#0088cc"),
            ("💾", "Save Data", "savedata", "#27ae60"),
            ("🏁", "End Session", "endsession", "#c0392b")
        ]
        
        for icon, name, node_type, color in blocks:
            self.add_block(icon, name, node_type, color)
        print("📦 [PALETTE] create_blocks END")
    
    def add_block(self, icon: str, name: str, node_type: str, color: str):
        print(f"➕ [PALETTE] add_block: {node_type} - {name}")
        widget = QFrame()
        widget.setFixedHeight(50)
        widget.setStyleSheet(f"""
            QFrame {{
                background-color: #2a2a2a;
                border-radius: 6px;
                border: 1px solid #3a3a3a;
            }}
            QFrame:hover {{
                background-color: #333;
                border: 1px solid {color};
            }}
        """)
        widget.setCursor(Qt.CursorShape.PointingHandCursor)
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(12)
        
        icon_label = QLabel(icon)
        icon_label.setFixedSize(36, 36)
        icon_label.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                border-radius: 6px;
                font-size: 18px;
                qproperty-alignment: AlignCenter;
            }}
        """)
        layout.addWidget(icon_label)
        
        name_label = QLabel(name)
        name_label.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
        layout.addWidget(name_label, 1)
        
        plus = QLabel("+")
        plus.setStyleSheet("color: #666; font-size: 16px; font-weight: bold;")
        layout.addWidget(plus)
        
        widget.mousePressEvent = lambda e, nt=node_type, ic=icon, n=name, c=color: self.start_drag(e, nt, ic, n, c)
        
        self.container_layout.insertWidget(self.container_layout.count() - 1, widget)
        print(f"✅ [PALETTE] add_block complete: {node_type}")
    
    def start_drag(self, event, node_type: str, icon: str, name: str, color: str):
        print(f"🚀 [PALETTE] start_drag - BEGIN: node_type={node_type}, name={name}")
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"🖱️ [PALETTE] Left button detected, creating drag...")
            drag = QDrag(self)
            mime = QMimeData()
            data = json.dumps({"type": node_type, "name": name, "color": color})
            mime.setText(data)
            print(f"📄 [PALETTE] Mime data set: {data}")
            drag.setMimeData(mime)
            
            # Создаем pixmap для отображения при перетаскивании
            pixmap = QPixmap(120, 40)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setBrush(QBrush(QColor(color)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(0, 0, 120, 40, 6, 6)
            painter.setPen(QPen(QColor("white")))
            painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            painter.drawText(QRect(40, 0, 80, 40), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name)
            painter.setFont(QFont("Arial", 16))
            painter.drawText(QRect(5, 0, 35, 40), Qt.AlignmentFlag.AlignCenter, icon)
            painter.end()
            
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(15, 20))
            
            print(f"🎨 [PALETTE] Pixmap created, hot spot set")
            result = drag.exec(Qt.DropAction.CopyAction)
            print(f"🏁 [PALETTE] Drag finished with result: {result}")
        else:
            print(f"⚠️ [PALETTE] Not left button, ignoring")
        print(f"🚀 [PALETTE] start_drag - END")