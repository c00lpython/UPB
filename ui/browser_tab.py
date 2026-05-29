from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl, QTimer


class BrowserTab(QWidget):
    """Отдельная вкладка браузера (только сайт, DevTools отдельно)"""
    
    def __init__(self, profile, tab_id: int, url: str = "https://google.com", parent=None):
        super().__init__(parent)
        
        self.profile = profile
        self.tab_id = tab_id
        self.devtools_view = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Панель навигации
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(5)
        
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
        
        # Только сайт (без DevTools внутри вкладки)
        self.site_view = QWebEngineView()
        
        # Создаём DevTools, но пока не связываем
        self.devtools_view = QWebEngineView()
        self.devtools_view.setStyleSheet("background-color: #1e1e1e; border-left: 1px solid #787878;")
        
        # Добавляем только сайт в вкладку
        layout.addLayout(nav_layout)
        layout.addWidget(self.site_view)
        
        # Сигналы
        self.back_btn.clicked.connect(self.site_view.back)
        self.forward_btn.clicked.connect(self.site_view.forward)
        self.refresh_btn.clicked.connect(self.site_view.reload)
        self.url_bar.returnPressed.connect(self.navigate)
        self.site_view.urlChanged.connect(self.update_url)
        self.site_view.titleChanged.connect(self.update_title)
        
        self.current_title = "New Tab"
        
        # Загружаем URL
        if isinstance(url, str) and url:
            self.set_url(url)
        else:
            self.set_url("https://google.com")
        
        # ВАЖНО: откладываем связывание DevTools до полной загрузки страницы
        # Это решает проблему чёрного экрана на первой вкладке!
        self.site_view.loadFinished.connect(self._on_load_finished)
    
    def _on_load_finished(self, ok):
        """Когда страница полностью загружена - связываем DevTools"""
        if ok:
            # Небольшая задержка для уверенности
            QTimer.singleShot(500, self._connect_devtools)
    
    def _connect_devtools(self):
        """Связываем сайт с его DevTools (вызывается после загрузки страницы)"""
        if self.devtools_view:
            try:
                # Пробуем setDevToolsPage
                self.site_view.page().setDevToolsPage(self.devtools_view.page())
                print(f"✅ DevTools connected for tab {self.tab_id} (setDevToolsPage)")
            except AttributeError:
                try:
                    # Альтернативный метод
                    self.site_view.page().setInspectedPage(self.devtools_view.page())
                    print(f"✅ DevTools connected for tab {self.tab_id} (setInspectedPage)")
                except AttributeError as e:
                    print(f"⚠️ Could not connect DevTools for tab {self.tab_id}: {e}")
    
    def set_url(self, url: str):
        if not url.startswith("http"):
            url = "https://" + url
        self.site_view.setUrl(QUrl(url))
    
    def navigate(self):
        url = self.url_bar.text()
        self.set_url(url)
    
    def update_url(self, url: QUrl):
        self.url_bar.setText(url.toString())
    
    def update_title(self, title: str):
        self.current_title = title[:30]
    
    def get_current_url(self) -> str:
        return self.site_view.url().toString()
    
    def get_site_view(self):
        return self.site_view
    
    def get_devtools_view(self):
        return self.devtools_view
    
    def get_tab_data(self):
        return {
            "url": self.get_current_url(),
            "title": self.current_title,
            "tab_id": self.tab_id
        }