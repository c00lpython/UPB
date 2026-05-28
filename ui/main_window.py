from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFrame, QLabel, QPushButton, QTextEdit,
    QStackedWidget
)
from PyQt6.QtCore import Qt, QDateTime, QObject, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWebEngineCore import QWebEnginePage

from ui.browser_widget import BrowserWidget
from ui.devtools_panel import DevToolsPanel
from ui.vm_table import VmTable

import os
import json


class CustomWebEnginePage(QWebEnginePage):
    """Кастомная страница для перехвата console.log"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
    
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        """Перехватывает сообщения из console.log"""
        if message.startswith('[UPB_SELECT]'):
            try:
                json_str = message.replace('[UPB_SELECT]', '')
                data = json.loads(json_str)
                
                if self.main_window:
                    self.main_window.on_selector_captured(
                        url=data.get('url', ''),
                        xpath=data.get('xpath', ''),
                        text=data.get('text', ''),
                        tag=data.get('tag', ''),
                        alt=data.get('alt', '')
                    )
            except json.JSONDecodeError as e:
                print(f"JSON parse error: {e}")
        else:
            super().javaScriptConsoleMessage(level, message, lineNumber, sourceID)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("UPB - Universal Parser Builder")
        self.setGeometry(100, 100, 1400, 900)
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.drag_pos = None
        
        os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '9222'
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d2d;
            }
            QSplitter::handle {
                background-color: #787878;
            }
        """)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.create_top_bar()
        main_layout.addWidget(self.top_bar)
        
        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.create_browser_view())
        self.content_stack.addWidget(self.create_project_panel())
        self.content_stack.addWidget(self.create_vm_panel())
        self.content_stack.addWidget(self.create_build_panel())
        self.content_stack.addWidget(self.create_test_panel())
        main_layout.addWidget(self.content_stack, 1)
        
        self.create_bottom_panel()
        main_layout.addWidget(self.bottom_frame)
        
        self.log("UPB Ready | Select mode: OFF")
    
    def create_top_bar(self):
        self.top_bar = QFrame()
        self.top_bar.setMaximumHeight(40)
        self.top_bar.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-bottom: 1px solid #787878;
            }
        """)
        
        layout = QHBoxLayout(self.top_bar)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(20)
        
        logo = QLabel("UPB")
        logo.setStyleSheet("color: #0e639c; font-weight: bold; font-size: 14px;")
        layout.addWidget(logo)
        
        separator = QLabel("│")
        separator.setStyleSheet("color: #787878;")
        layout.addWidget(separator)
        
        self.tab_browser = QPushButton("Browser")
        self.tab_project = QPushButton("Project")
        self.tab_vm = QPushButton("VM")
        self.tab_build = QPushButton("Build")
        self.tab_test = QPushButton("Test")
        
        tab_style = """
            QPushButton {
                background-color: transparent;
                color: #cccccc;
                padding: 8px 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
                color: #ffffff;
            }
        """
        
        for tab in [self.tab_browser, self.tab_project, self.tab_vm, self.tab_build, self.tab_test]:
            tab.setStyleSheet(tab_style)
            layout.addWidget(tab)
        
        layout.addStretch()
        
        self.btn_min = QPushButton("—")
        self.btn_max = QPushButton("□")
        self.btn_close = QPushButton("✕")
        
        btn_style = """
            QPushButton {
                background-color: transparent;
                color: #cccccc;
                padding: 6px 12px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
                color: #ffffff;
            }
        """
        
        close_style = """
            QPushButton {
                background-color: transparent;
                color: #cccccc;
                padding: 6px 12px;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #e81123;
                color: #ffffff;
            }
        """
        
        self.btn_min.setStyleSheet(btn_style)
        self.btn_max.setStyleSheet(btn_style)
        self.btn_close.setStyleSheet(close_style)
        
        self.btn_min.clicked.connect(self.showMinimized)
        self.btn_max.clicked.connect(self.toggle_maximized)
        self.btn_close.clicked.connect(self.close)
        
        layout.addWidget(self.btn_min)
        layout.addWidget(self.btn_max)
        layout.addWidget(self.btn_close)
        
        self.tab_browser.clicked.connect(lambda: self.switch_tab(0))
        self.tab_project.clicked.connect(lambda: self.switch_tab(1))
        self.tab_vm.clicked.connect(lambda: self.switch_tab(2))
        self.tab_build.clicked.connect(lambda: self.switch_tab(3))
        self.tab_test.clicked.connect(lambda: self.switch_tab(4))
        
        self.tab_browser.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px 12px;
                border: none;
            }
        """)
        self.current_tab_index = 0
    
    def create_browser_view(self):
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.browser_widget = BrowserWidget()
        
        custom_page = CustomWebEnginePage(self)
        self.browser_widget.web_view.setPage(custom_page)
        
        self.devtools_panel = DevToolsPanel()
        self.devtools_panel.attach_to_browser(self.browser_widget)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.browser_widget)
        splitter.addWidget(self.devtools_panel)
        splitter.setSizes([850, 150])
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("QSplitter::handle { background-color: #787878; }")
        
        layout.addWidget(splitter)
        return panel
    
    def create_project_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel("📁 Project Management\n\n"
                      "• New Project — создать новый проект\n"
                      "• Load Project — загрузить существующий\n"
                      "• Save Project — сохранить текущий\n"
                      "• Settings — настройки проекта")
        label.setStyleSheet("color: #cccccc; font-size: 14px; padding: 20px;")
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(label)
        return widget
    
    def create_vm_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.vm_table = VmTable()
        layout.addWidget(self.vm_table)
        return widget
    
    def create_build_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel("🔧 Build Configuration\n\n"
                      "• Output format: Excel (.xlsx)\n"
                      "• Telegram bot: coming soon...\n"
                      "• Target folder: ./projects/\n"
                      "• Parser name: [PROJECT_NAME]Parser.py")
        label.setStyleSheet("color: #cccccc; font-size: 14px; padding: 20px;")
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(label)
        return widget
    
    def create_test_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel("🧪 Test Mode\n\n"
                      "• Run parser in debug mode\n"
                      "• Preview results before build\n"
                      "• Check variables extraction\n"
                      "• Validate XPath selectors")
        label.setStyleSheet("color: #cccccc; font-size: 14px; padding: 20px;")
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(label)
        return widget
    
    def create_bottom_panel(self):
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(5, 2, 5, 2)
        bottom_layout.setSpacing(10)
        
        console_container = QWidget()
        console_container.setMaximumHeight(80)
        console_layout = QVBoxLayout(console_container)
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_layout.setSpacing(2)
        
        self.console_label = QLabel("v1 | console: Ready")
        self.console_label.setStyleSheet("color: #cccccc; font-family: Consolas; font-size: 11px; padding: 2px;")
        
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setMaximumHeight(60)
        self.console_text.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                color: #cccccc;
                font-family: Consolas;
                font-size: 11px;
                border: 1px solid #787878;
            }
        """)
        
        console_layout.addWidget(self.console_label)
        console_layout.addWidget(self.console_text)
        
        tools_widget = QWidget()
        tools_widget.setMaximumHeight(80)
        tools_widget.setMaximumWidth(200)
        tools_layout = QHBoxLayout(tools_widget)
        tools_layout.setSpacing(5)
        
        self.btn_select = QPushButton("Select")
        self.btn_select.setCheckable(True)
        self.btn_build = QPushButton("Build")
        self.btn_run = QPushButton("Run")
        
        btn_style = """
            QPushButton {
                background-color: #3c3c3c;
                color: #cccccc;
                padding: 6px 12px;
                border: 1px solid #787878;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
                color: #ffffff;
            }
            QPushButton:checked {
                background-color: #0e639c;
                color: #ffffff;
                border: 1px solid #0e639c;
            }
        """
        
        self.btn_select.setStyleSheet(btn_style)
        self.btn_build.setStyleSheet(btn_style)
        self.btn_run.setStyleSheet(btn_style)
        
        tools_layout.addWidget(self.btn_select)
        tools_layout.addWidget(self.btn_build)
        tools_layout.addWidget(self.btn_run)
        tools_layout.addStretch()
        
        bottom_layout.addWidget(console_container, 1)
        bottom_layout.addWidget(tools_widget)
        
        self.bottom_frame = QFrame()
        self.bottom_frame.setLayout(bottom_layout)
        self.bottom_frame.setMaximumHeight(80)
        self.bottom_frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border-top: 1px solid #787878;
            }
        """)
        
        self.btn_select.clicked.connect(self.toggle_select_mode)
        self.btn_build.clicked.connect(self.on_build_clicked)
        self.btn_run.clicked.connect(self.on_run_clicked)
    
    def switch_tab(self, index: int):
        self.content_stack.setCurrentIndex(index)
        self.current_tab_index = index
        
        tab_style_normal = """
            QPushButton {
                background-color: transparent;
                color: #cccccc;
                padding: 8px 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #3c3c3c;
                color: #ffffff;
            }
        """
        
        tab_style_active = """
            QPushButton {
                background-color: #3c3c3c;
                color: #ffffff;
                padding: 8px 12px;
                border: none;
            }
        """
        
        tabs = [self.tab_browser, self.tab_project, self.tab_vm, self.tab_build, self.tab_test]
        for i, tab in enumerate(tabs):
            if i == index:
                tab.setStyleSheet(tab_style_active)
            else:
                tab.setStyleSheet(tab_style_normal)
        
        tab_names = ["Browser", "Project", "VM", "Build", "Test"]
        self.log(f"Switched to {tab_names[index]} tab")
    
    def toggle_maximized(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def log(self, message: str):
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        self.console_text.append(f"[{timestamp}] {message}")
        scrollbar = self.console_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_selector_captured(self, url: str, xpath: str, text: str, tag: str, alt: str = ""):
        self.log("=" * 50)
        self.log("🎯 НОВЫЙ ЭЛЕМЕНТ ВЫДЕЛЕН:")
        self.log(f"   🌐 URL: {url}")
        self.log(f"   📍 XPath: {xpath}")
        self.log(f"   📝 Text: {text[:50] if text else '(empty)'}")
        self.log(f"   🏷️  Tag: {tag}")
        if alt:
            self.log(f"   🖼️  Alt: {alt}")
        
        if hasattr(self, 'vm_table'):
            self.vm_table.import_from_select(
                url=url,
                xpath=xpath,
                text=text,
                tag=tag,
                alt=alt
            )
            self.log(f"✅ Переменная добавлена в VM таблицу")
        self.log("=" * 50)
    
    def toggle_select_mode(self):
        if self.btn_select.isChecked():
            self.log("Select mode: ON — кликните на элемент для сохранения XPath и URL")
            self.enable_select_mode()
        else:
            self.log("Select mode: OFF")
            self.disable_select_mode()
    
    def enable_select_mode(self):
        js = """
        (function() {
            if (window.upb_select_active) return;
            
            window.upb_select_active = true;
            document.body.style.cursor = 'crosshair';
            
            function getXPath(element) {
                if (element.id !== '')
                    return '//*[@id="' + element.id + '"]';
                if (element === document.body)
                    return '/html/body';
                
                var ix = 0;
                var siblings = element.parentNode.childNodes;
                for (var i = 0; i < siblings.length; i++) {
                    var sibling = siblings[i];
                    if (sibling === element)
                        return getXPath(element.parentNode) + '/' + 
                               element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                        ix++;
                }
            }
            
            window.upb_click_handler = function(e) {
                if (!window.upb_select_active) return;
                
                e.stopPropagation();
                e.preventDefault();
                
                var xpath = getXPath(e.target);
                var text = e.target.innerText.substring(0, 100);
                var tag = e.target.tagName;
                var url = window.location.href;
                
                var alt = "";
                if (tag.toUpperCase() === "IMG") {
                    alt = e.target.getAttribute("alt") || "";
                }
                
                console.log('[UPB_SELECT]' + JSON.stringify({
                    url: url,
                    xpath: xpath,
                    text: text,
                    tag: tag,
                    alt: alt
                }));
                
                var originalBg = e.target.style.backgroundColor;
                e.target.style.backgroundColor = '#ff4444';
                setTimeout(function() {
                    e.target.style.backgroundColor = originalBg;
                }, 300);
                
                return false;
            };
            
            document.addEventListener('click', window.upb_click_handler, true);
        })();
        """
        self.browser_widget.web_view.page().runJavaScript(js)
    
    def disable_select_mode(self):
        js = """
        (function() {
            window.upb_select_active = false;
            document.body.style.cursor = 'default';
            if (window.upb_click_handler) {
                document.removeEventListener('click', window.upb_click_handler, true);
            }
        })();
        """
        self.browser_widget.web_view.page().runJavaScript(js)
    
    def on_build_clicked(self):
        self.log("Build started... (placeholder)")
        self.log("Build completed! Parser generated.")
    
    def on_run_clicked(self):
        self.log("Running parser... (placeholder)")
        self.log("Parser execution completed.")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if event.pos().y() <= 40:
                self.drag_pos = event.globalPosition().toPoint()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_pos:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()
    
    def mouseReleaseEvent(self, event):
        self.drag_pos = None
    
    def keyPressEvent(self, event: QKeyEvent):
        if (event.modifiers() & Qt.KeyboardModifier.ControlModifier and 
            event.modifiers() & Qt.KeyboardModifier.ShiftModifier and 
            event.key() == Qt.Key.Key_C):
            self.btn_select.toggle()
            self.toggle_select_mode()
        else:
            super().keyPressEvent(event)