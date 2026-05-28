from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl


class BrowserWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        nav_layout = QHBoxLayout()
        self.back_btn = QPushButton("◀")
        self.forward_btn = QPushButton("▶")
        self.refresh_btn = QPushButton("⟳")
        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL and press Enter...")
        
        nav_style = """
            QPushButton {
                background-color: #3c3c3c;
                color: #cccccc;
                border: 1px solid #787878;
                padding: 5px 10px;
            }
            QPushButton:hover { background-color: #4c4c4c; }
            QLineEdit {
                background-color: #3c3c3c;
                color: #cccccc;
                border: 1px solid #787878;
                padding: 5px;
            }
        """
        
        for btn in [self.back_btn, self.forward_btn, self.refresh_btn]:
            btn.setStyleSheet(nav_style)
        self.url_bar.setStyleSheet(nav_style)
        
        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.forward_btn)
        nav_layout.addWidget(self.refresh_btn)
        nav_layout.addWidget(self.url_bar)
        
        self.web_view = QWebEngineView()
        
        layout.addLayout(nav_layout)
        layout.addWidget(self.web_view)
        
        self.back_btn.clicked.connect(self.web_view.back)
        self.forward_btn.clicked.connect(self.web_view.forward)
        self.refresh_btn.clicked.connect(self.web_view.reload)
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.web_view.urlChanged.connect(self.update_url_bar)
        
        self.web_view.setUrl(QUrl("https://www.google.com"))
    
    def navigate_to_url(self):
        url = self.url_bar.text()
        if not url.startswith("http"):
            url = "https://" + url
        self.web_view.setUrl(QUrl(url))
    
    def update_url_bar(self, url: QUrl):
        self.url_bar.setText(url.toString())
    
    def get_web_view(self):
        return self.web_view