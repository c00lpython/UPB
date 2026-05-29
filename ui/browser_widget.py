from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal

from ui.browser_tab import BrowserTab


class BrowserWidget(QWidget):
    """Браузер с поддержкой множества вкладок"""
    
    url_changed = pyqtSignal(str)
    devtools_changed = pyqtSignal(object)
    selector_captured = pyqtSignal(str, str, str, str, str)  # url, xpath, text, tag, alt
    
    def __init__(self, profile, parent=None):
        super().__init__(parent)
        self.profile = profile
        self.next_tab_id = 1
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        tabs_bar = QHBoxLayout()
        tabs_bar.setSpacing(5)
        
        self.btn_new_tab = QPushButton("➕")
        self.btn_new_tab.setMaximumWidth(30)
        self.btn_new_tab.clicked.connect(self.add_new_tab)
        self.btn_new_tab.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: #cccccc;
                border: 1px solid #787878;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
                color: #ffffff;
            }
        """)
        
        tabs_bar.addWidget(self.btn_new_tab)
        tabs_bar.addStretch()
        
        layout.addLayout(tabs_bar)
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #787878;
                background-color: #2d2d2d;
            }
            QTabBar::tab {
                background-color: #3c3c3c;
                color: #cccccc;
                padding: 5px 10px;
            }
            QTabBar::tab:selected {
                background-color: #2d2d2d;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #4c4c4c;
            }
            QTabBar::close-button {
                subcontrol-position: right;
                padding-right: 5px;
            }
        """)
        
        layout.addWidget(self.tab_widget)
        
        self.add_new_tab()
    
    def add_new_tab(self, url: str = "https://google.com"):
        tab = BrowserTab(self.profile, self.next_tab_id, url)
        index = self.tab_widget.addTab(tab, "New Tab")
        self.tab_widget.setCurrentIndex(index)
        self.next_tab_id += 1
        
        # Подключаем сигналы
        tab.site_view.titleChanged.connect(lambda title, idx=index: self.update_tab_title(idx, title))
        tab.selector_captured.connect(self.selector_captured.emit)  # Передаём сигнал дальше
        self.devtools_changed.emit(tab.get_devtools_view())
        
        return tab
    
    def close_tab(self, index: int):
        if self.tab_widget.count() == 1:
            self.add_new_tab()
        self.tab_widget.removeTab(index)
    
    def on_tab_changed(self, index: int):
        if index >= 0:
            tab = self.tab_widget.widget(index)
            if tab:
                url = tab.get_current_url()
                self.url_changed.emit(url)
                self.devtools_changed.emit(tab.get_devtools_view())
                print(f"🔄 Tab changed to {index}: {url}")
    
    def update_tab_title(self, index: int, title: str):
        short_title = title[:25] + "..." if len(title) > 25 else title
        self.tab_widget.setTabText(index, short_title)
    
    def get_current_tab(self):
        return self.tab_widget.currentWidget()
    
    def get_current_web_view(self):
        current_tab = self.get_current_tab()
        if current_tab:
            return current_tab.get_site_view()
        return None
    
    def get_web_view(self):
        return self.get_current_web_view()
    
    def get_all_tabs_data(self) -> list:
        tabs_data = []
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if tab:
                tabs_data.append(tab.get_tab_data())
        return tabs_data
    
    def restore_tabs(self, tabs_data: list):
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        
        if tabs_data:
            for tab_data in tabs_data:
                self.add_new_tab(tab_data.get("url", "https://google.com"))
        else:
            self.add_new_tab()