from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
import socket
import threading


class DevToolsPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #1e1e1e; border-left: 1px solid #787878;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.devtools_view = QWebEngineView()
        layout.addWidget(self.devtools_view)
    
    def attach_to_browser(self, browser_widget):
        """Связывает DevTools с браузером через Remote Debugging"""
        browser_view = browser_widget.get_web_view()
        
        # Включаем Remote Debugging
        import os
        os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '9222'
        
        # Загружаем DevTools из Chrome
        self.devtools_view.setUrl(QUrl("http://localhost:9222"))