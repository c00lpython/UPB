# ui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFrame, QLabel, QPushButton, QTextEdit,
    QStackedWidget, QListWidget, QListWidgetItem, QLineEdit,
    QGroupBox, QGridLayout, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt, QDateTime, QUrl, QTimer, Signal
from PySide6.QtGui import QKeyEvent
from ui.browser_widget import BrowserWidget
from ui.vm_table import VmTable
from ui.SE.script_editor import ScriptEditor
from core.project_manager import ProjectManager

import os
import json
import uuid


class MainWindow(QMainWindow):
    def __init__(self, profile=None):
        super().__init__()
        self.setWindowTitle("UPB - Universal Parser Builder")
        self.setGeometry(100, 100, 1400, 900)
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.drag_pos = None
        
        self.profile = profile
        self.project_manager = ProjectManager()
        
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
        self.content_stack.addWidget(self.create_script_editor_panel())  # Script Editor
        main_layout.addWidget(self.content_stack, 1)
        
        self.create_bottom_panel()
        main_layout.addWidget(self.bottom_frame)
        self.log("UPB Ready | Select mode: OFF")
        
        self._browser_ready = False
        QTimer.singleShot(500, self._set_browser_ready)
        QTimer.singleShot(2000, self.auto_open_latest_project)
        
        self.log("UPB Ready | Select mode: OFF")

    def _set_browser_ready(self):
        self._browser_ready = True
    
    def auto_open_latest_project(self):
        if not self._browser_ready:
            QTimer.singleShot(500, self.auto_open_latest_project)
            return
        last_project = self.project_manager.get_latest_project()
        if not last_project:
            return
        for i in range(self.project_list.count()):
            item = self.project_list.item(i)
            project_name = item.text().replace("📂  ", "")
            if project_name == last_project:
                self.project_list.setCurrentRow(i)
                self.on_open_project()
                self.log(f"📂 Auto-opened: {last_project}")
                return
            
    def view_variable_in_browser(self, url: str, xpath: str):
        """Открывает URL в новой вкладке и выделяет элемент по XPath"""
        print(f"\n{'='*60}")
        print(f"🌐 [View in Browser] Запрос на открытие")
        print(f"   URL: {url}")
        print(f"   XPath: {xpath}")
        print(f"{'='*60}\n")
        
        if not hasattr(self, 'browser_widget') or not self.browser_widget:
            self.log("❌ Browser not available")
            QMessageBox.warning(self, "No Browser", "Browser widget is not available!")
            return
        
        if not url:
            self.log("❌ No URL for this variable")
            QMessageBox.warning(self, "No URL", "This variable has no URL defined!")
            return
        
        try:
            tab = self.browser_widget.add_new_tab(url)
            
            if tab and xpath:
                safe_xpath = xpath.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
                
                js_code = f"""
                (function() {{
                    try {{
                        // Убираем предыдущие подсветки
                        document.querySelectorAll('.upb-overlay, .upb-corner, .upb-label, .upb-margin, .upb-padding').forEach(el => el.remove());
                        
                        // Ищем элемент по XPath
                        let xpath = "{safe_xpath}";
                        let result = document.evaluate(xpath, document, null, 
                            XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                        let element = result.singleNodeValue;
                        
                        if (!element) {{
                            console.log('%c❌ UPB: Element not found', 'color: #ff0000; font-weight: bold;');
                            return '❌ Element not found';
                        }}
                        
                        // Скроллим к элементу
                        element.scrollIntoView({{behavior: 'smooth', block: 'center', inline: 'center'}});
                        
                        // Получаем размеры и позицию элемента
                        let rect = element.getBoundingClientRect();
                        let top = rect.top + window.scrollY;
                        let left = rect.left + window.scrollX;
                        let width = rect.width;
                        let height = rect.height;
                        
                        // Создаём оверлей (полупрозрачная заливка)
                        let overlay = document.createElement('div');
                        overlay.className = 'upb-overlay';
                        overlay.style.cssText = `
                            position: absolute;
                            top: ${{top}}px;
                            left: ${{left}}px;
                            width: ${{width}}px;
                            height: ${{height}}px;
                            background: rgba(0, 120, 212, 0.1);
                            pointer-events: none;
                            z-index: 999998;
                            transition: all 0.2s ease;
                        `;
                        document.body.appendChild(overlay);
                        
                        // Функция создания уголка
                        function createCorner(x, y, rotate) {{
                            let corner = document.createElement('div');
                            corner.className = 'upb-corner';
                            corner.style.cssText = `
                                position: absolute;
                                top: ${{y}}px;
                                left: ${{x}}px;
                                width: 12px;
                                height: 12px;
                                border: 2px solid #0078d4;
                                background: transparent;
                                pointer-events: none;
                                z-index: 999999;
                                transform: rotate(${{rotate}}deg);
                                transition: all 0.2s ease;
                            `;
                            document.body.appendChild(corner);
                            return corner;
                        }}
                        
                        // 4 уголка
                        createCorner(left - 6, top - 6, 0);      //左上
                        createCorner(left + width - 6, top - 6, 90);   //右上
                        createCorner(left + width - 6, top + height - 6, 180); //右下
                        createCorner(left - 6, top + height - 6, 270);  //左下
                        
                        // Метка UPB
                        let label = document.createElement('div');
                        label.className = 'upb-label';
                        label.style.cssText = `
                            position: absolute;
                            top: ${{top - 30}}px;
                            left: ${{left}}px;
                            background: #0078d4;
                            color: white;
                            padding: 3px 10px;
                            font-size: 11px;
                            font-weight: bold;
                            font-family: 'Segoe UI', Arial, sans-serif;
                            border-radius: 3px;
                            pointer-events: none;
                            z-index: 999999;
                            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                            letter-spacing: 1px;
                        `;
                        label.textContent = '🎯 UPB • ' + element.tagName.toLowerCase();
                        document.body.appendChild(label);
                        
                        // Пульсация уголков
                        let pulseCount = 0;
                        let pulseInterval = setInterval(() => {{
                            let color = pulseCount % 2 === 0 ? '#ff8800' : '#0078d4';
                            document.querySelectorAll('.upb-corner').forEach(c => {{
                                c.style.borderColor = color;
                            }});
                            pulseCount++;
                            if (pulseCount >= 6) {{
                                clearInterval(pulseInterval);
                                document.querySelectorAll('.upb-corner').forEach(c => {{
                                    c.style.borderColor = '#0078d4';
                                }});
                            }}
                        }}, 500);
                        
                        // Клик для снятия
                        document.addEventListener('click', function cleanup(e) {{
                            document.querySelectorAll('.upb-overlay, .upb-corner, .upb-label').forEach(el => el.remove());
                            document.removeEventListener('click', cleanup);
                            clearInterval(pulseInterval);
                        }}, {{once: true}});
                        
                        // Обновление при скролле/ресайзе
                        function updatePosition() {{
                            let newRect = element.getBoundingClientRect();
                            overlay.style.top = (newRect.top + window.scrollY) + 'px';
                            overlay.style.left = (newRect.left + window.scrollX) + 'px';
                            overlay.style.width = newRect.width + 'px';
                            overlay.style.height = newRect.height + 'px';
                            
                            let corners = document.querySelectorAll('.upb-corner');
                            if (corners.length === 4) {{
                                corners[0].style.top = (newRect.top + window.scrollY - 6) + 'px';
                                corners[0].style.left = (newRect.left + window.scrollX - 6) + 'px';
                                corners[1].style.top = (newRect.top + window.scrollY - 6) + 'px';
                                corners[1].style.left = (newRect.left + window.scrollX + newRect.width - 6) + 'px';
                                corners[2].style.top = (newRect.top + window.scrollY + newRect.height - 6) + 'px';
                                corners[2].style.left = (newRect.left + window.scrollX + newRect.width - 6) + 'px';
                                corners[3].style.top = (newRect.top + window.scrollY + newRect.height - 6) + 'px';
                                corners[3].style.left = (newRect.left + window.scrollX - 6) + 'px';
                            }}
                            
                            label.style.top = (newRect.top + window.scrollY - 30) + 'px';
                            label.style.left = (newRect.left + window.scrollX) + 'px';
                        }}
                        
                        window.addEventListener('scroll', updatePosition, {{passive: true}});
                        window.addEventListener('resize', updatePosition, {{passive: true}});
                        
                        // Сохраняем ссылки для очистки
                        window._upb_cleanup = () => {{
                            document.querySelectorAll('.upb-overlay, .upb-corner, .upb-label').forEach(el => el.remove());
                            window.removeEventListener('scroll', updatePosition);
                            window.removeEventListener('resize', updatePosition);
                        }};
                        
                        console.log('%c✅ UPB: Element highlighted %c' + element.tagName, 
                            'color: #00ff00; font-weight: bold;', 'color: #fff;');
                        
                        return '✅ Element highlighted: ' + element.tagName;
                        
                    }} catch(e) {{
                        console.error('❌ UPB Error:', e.message);
                        return '❌ Error: ' + e.message;
                    }}
                }})();
                """
                
                def highlight_on_load(ok):
                    if ok:
                        tab.site_view.page().runJavaScript(js_code, 
                            lambda result: print(f"🔍 {result}"))
                        self.log(f"🎯 Element highlighted with corner overlay")
                
                tab.site_view.loadFinished.connect(highlight_on_load)
            
            self.log(f"🌐 Opened new tab: {url[:60]}...")
            self.switch_tab(0)
            
        except Exception as e:
            self.log(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

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
        self.tab_script = QPushButton("Script Editor")
        
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
        
        for tab in [self.tab_browser, self.tab_project, self.tab_vm, 
                    self.tab_build, self.tab_test, self.tab_script]:
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
        self.tab_script.clicked.connect(lambda: self.switch_tab(5))
        
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
        """Создаёт браузер с профилем из открытого проекта или временный"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        from PySide6.QtWebEngineCore import QWebEngineProfile
        
        # Проверяем, есть ли открытый проект
        if self.project_manager and self.project_manager.current_project:
            project_path = os.path.join(self.project_manager.projects_dir, self.project_manager.current_project)
            profile_path = os.path.join(project_path, "profile")
            
            # Создаём папку профиля если её нет
            os.makedirs(profile_path, exist_ok=True)
            
            # Используем профиль проекта
            profile = QWebEngineProfile(f"UPB_{self.project_manager.current_project}")
            profile.setPersistentStoragePath(profile_path)
            profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
            )
            
            print(f"\n{'='*70}")
            print(f"🔧 [MAIN] ЗАГРУЗКА ПРОФИЛЯ ПРОЕКТА")
            print(f"{'='*70}")
            print(f"   📁 Проект: {self.project_manager.current_project}")
            print(f"   📁 Путь профиля: {profile_path}")
            print(f"   🍪 Политика кук: ForcePersistentCookies")
            print(f"{'='*70}\n")
            
        else:
            # Нет открытого проекта — создаём временный профиль
            temp_id = str(uuid.uuid4())[:8]
            profile = QWebEngineProfile(f"Temporary_{temp_id}")
            profile.setPersistentStoragePath(f"temp_profile_{temp_id}")
            profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
            )
            
            print(f"\n{'='*70}")
            print(f"🔧 [MAIN] СОЗДАНИЕ ВРЕМЕННОГО БРАУЗЕРА")
            print(f"{'='*70}")
            print(f"   📁 Путь хранения: {profile.persistentStoragePath()}")
            print(f"   🍪 Политика кук: NoPersistentCookies")
            print(f"   🆔 ID: {temp_id}")
            print(f"{'='*70}\n")
        
        # Создаём виджет браузера
        self.browser_widget = BrowserWidget(profile)
        
        # Подключаем сигналы
        self.browser_widget.url_changed.connect(self.on_browser_url_changed)
        self.browser_widget.devtools_changed.connect(self.on_devtools_changed)
        self.browser_widget.selector_captured.connect(self.on_selector_captured)
        
        # Контейнер для DevTools
        self.devtools_container = QWidget()
        self.devtools_container.setStyleSheet("background-color: #1e1e1e; border-left: 1px solid #787878;")
        self.devtools_container_layout = QVBoxLayout(self.devtools_container)
        self.devtools_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.current_devtools_view = None
        
        # Разделитель (браузер + DevTools)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.browser_widget)
        splitter.addWidget(self.devtools_container)
        splitter.setSizes([850, 150])
        splitter.setHandleWidth(2)
        splitter.setStyleSheet("QSplitter::handle { background-color: #787878; }")
        
        layout.addWidget(splitter)
        return panel

    def on_browser_url_changed(self, url: str):
        self.log(f"📍 URL changed: {url}")

    def on_devtools_changed(self, devtools_view):
        if self.current_devtools_view:
            self.devtools_container_layout.removeWidget(self.current_devtools_view)
            self.current_devtools_view.setParent(None)
        
        self.current_devtools_view = devtools_view
        self.devtools_container_layout.addWidget(self.current_devtools_view)

    def create_script_editor_panel(self):
        """Script Editor панель с n8n браузером и кастомными блоками"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.script_editor = ScriptEditor(project_manager=self.project_manager)
        self.script_editor.log_signal.connect(self.log)
        
        layout.addWidget(self.script_editor)
        return widget

    def create_project_panel(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        left_panel = QWidget()
        left_panel.setMaximumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        projects_label = QLabel("📁 PROJECTS")
        projects_label.setStyleSheet("color: #0e639c; font-weight: bold; font-size: 12px; padding: 5px;")
        left_layout.addWidget(projects_label)
        
        self.project_list = QListWidget()
        self.project_list.setStyleSheet("""
            QListWidget {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3c3c3c;
            }
            QListWidget::item:hover {
                background-color: #3c3c3c;
            }
            QListWidget::item:selected {
                background-color: #0e639c;
                color: #ffffff;
            }
        """)
        
        self.refresh_project_list()
        left_layout.addWidget(self.project_list)
        
        self.btn_new_project = QPushButton("➕ New Project")
        self.btn_new_project.setStyleSheet("""
            QPushButton {
                background-color: #0e639c;
                color: white;
                padding: 8px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
        """)
        left_layout.addWidget(self.btn_new_project)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        info_group = QGroupBox("📄 Project Details")
        info_group.setStyleSheet("""
            QGroupBox {
                color: #cccccc;
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(10)
        
        info_layout.addWidget(QLabel("Name:"), 0, 0)
        self.project_name = QLineEdit()
        self.project_name.setPlaceholderText("Project name")
        self.project_name.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                padding: 5px;
                border-radius: 3px;
            }
        """)
        self.project_name.setReadOnly(True)
        info_layout.addWidget(self.project_name, 0, 1)
        
        info_layout.addWidget(QLabel("Created:"), 1, 0)
        self.project_created = QLabel("—")
        self.project_created.setStyleSheet("color: #cccccc; padding: 5px;")
        info_layout.addWidget(self.project_created, 1, 1)
        
        info_layout.addWidget(QLabel("Modified:"), 2, 0)
        self.project_modified = QLabel("—")
        self.project_modified.setStyleSheet("color: #cccccc; padding: 5px;")
        info_layout.addWidget(self.project_modified, 2, 1)
        
        info_layout.addWidget(QLabel("Variables:"), 3, 0)
        self.project_vars_count = QLabel("0")
        self.project_vars_count.setStyleSheet("color: #0e639c; font-weight: bold; padding: 5px;")
        info_layout.addWidget(self.project_vars_count, 3, 1)
        
        right_layout.addWidget(info_group)
        
        vars_group = QGroupBox("📊 Variables Preview")
        vars_group.setStyleSheet("""
            QGroupBox {
                color: #cccccc;
                border: 1px solid #3c3c3c;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        vars_layout = QVBoxLayout(vars_group)
        self.vars_preview = QTextEdit()
        self.vars_preview.setReadOnly(True)
        self.vars_preview.setMaximumHeight(150)
        self.vars_preview.setStyleSheet("""
            QTextEdit {
                background-color: #252526;
                color: #cccccc;
                border: none;
                font-family: Consolas;
                font-size: 11px;
            }
        """)
        vars_layout.addWidget(self.vars_preview)
        
        right_layout.addWidget(vars_group)
        
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        self.btn_open = QPushButton("📂 Open Project")
        self.btn_save = QPushButton("💾 Save Project")
        self.btn_export = QPushButton("🚀 Export Parser")
        self.btn_delete = QPushButton("🗑 Delete")
        
        action_style = """
            QPushButton {
                background-color: #3c3c3c;
                color: #cccccc;
                padding: 8px 15px;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
                color: #ffffff;
            }
        """
        
        for btn in [self.btn_open, self.btn_save, self.btn_export, self.btn_delete]:
            btn.setStyleSheet(action_style)
            actions_layout.addWidget(btn)
        
        actions_layout.addStretch()
        right_layout.addLayout(actions_layout)
        
        layout.addWidget(left_panel)
        layout.addWidget(right_panel, 1)
        
        self.project_list.itemSelectionChanged.connect(self.on_project_selected)
        self.btn_new_project.clicked.connect(self.on_new_project)
        self.btn_save.clicked.connect(self.on_save_project)
        self.btn_open.clicked.connect(self.on_open_project)
        self.btn_export.clicked.connect(self.on_export_parser)
        self.btn_delete.clicked.connect(self.on_delete_project)
        
        if self.project_list.count() > 0:
            self.project_list.setCurrentRow(0)
        
        return widget

    def refresh_project_list(self):
        self.project_list.clear()
        projects = self.project_manager.get_all_projects()
        for project in projects:
            item = QListWidgetItem(f"📂  {project['name']}")
            item.setData(Qt.ItemDataRole.UserRole, project)
            self.project_list.addItem(item)

    def on_project_selected(self):
        current = self.project_list.currentItem()
        if current:
            project_data = current.data(Qt.ItemDataRole.UserRole)
            if project_data:
                self.project_name.setText(project_data['name'])
                self.project_created.setText(project_data['created'][:16] if project_data['created'] else "—")
                self.project_modified.setText(project_data['modified'][:16] if project_data['modified'] else "—")
                self.project_vars_count.setText(str(project_data['variables_count']))
                
                # Обновляем Script Editor с текущим проектом
                if hasattr(self, 'script_editor'):
                    self.script_editor.update_project(project_data['name'])
                
                if hasattr(self, 'vm_table') and self.project_manager.current_project == project_data['name']:
                    preview_text = ""
                    for row in range(self.vm_table.table.rowCount()):
                        name_item = self.vm_table.table.item(row, 0)
                        xpath_item = self.vm_table.table.item(row, 1)
                        if name_item and xpath_item:
                            preview_text += f"• {name_item.text()} → {xpath_item.text()[:50]}...\n"
                    self.vars_preview.setText(preview_text if preview_text else "No variables yet")
                else:
                    self.vars_preview.setText("Open project to see variables")

    def on_new_project(self):
        name, ok = QInputDialog.getText(self, "New Project", "Enter project name:")
        if ok and name:
            print(f"\n{'='*70}")
            print(f"🌟 [NEW PROJECT] Создание проекта: {name}")
            print(f"{'='*70}")
            
            success, result = self.project_manager.create_project(name)
            if success:
                from PySide6.QtWebEngineCore import QWebEngineProfile
                project_path = os.path.join(self.project_manager.projects_dir, name)
                profile_path = os.path.join(project_path, "profile")
                
                if not os.path.exists(profile_path):
                    os.makedirs(profile_path)
                
                profile = QWebEngineProfile(name)
                profile.setPersistentStoragePath(profile_path)
                profile.setPersistentCookiesPolicy(
                    QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
                )
                
                print(f"   📁 Профиль проекта: {profile_path}")
                print(f"   🍪 Политика: ForcePersistentCookies")
                print(f"{'='*70}\n")
                
                new_browser = BrowserWidget(profile)
                new_browser.url_changed.connect(self.on_browser_url_changed)
                new_browser.devtools_changed.connect(self.on_devtools_changed)
                new_browser.selector_captured.connect(self.on_selector_captured)
                
                self._replace_browser_widget(new_browser)
                self.refresh_project_list()
                self.project_manager.current_project = name
                self.project_manager.current_profile = profile
                
                # Обновляем Script Editor
                if hasattr(self, 'script_editor'):
                    self.script_editor.update_project(name)
                
                for i in range(self.project_list.count()):
                    item = self.project_list.item(i)
                    if item.text().replace("📂  ", "") == name:
                        self.project_list.setCurrentRow(i)
                        break
            else:
                QMessageBox.warning(self, "Error", f"Failed to create project: {result}")

    def on_save_project(self):
        current = self.project_list.currentItem()
        if not current:
            self.log("⚠️ No project selected")
            return
        
        project_name = current.text().replace("📂  ", "")
        
        variables = []
        if hasattr(self, 'vm_table'):
            variables = self.vm_table.get_all_variables()
        
        tabs_data = []
        current_tab = 0
        if hasattr(self, 'browser_widget'):
            tabs_data = self.browser_widget.get_all_tabs_data()
            current_tab = self.browser_widget.tab_widget.currentIndex()
        
        browser_data = {
            "tabs": tabs_data,
            "current_tab": current_tab,
            "history": []
        }
        
        success, result = self.project_manager.save_project(project_name, variables, browser_data)
        if success:
            self.log(f"✅ Project saved: {project_name}")
            self.refresh_project_list()
        else:
            QMessageBox.warning(self, "Error", f"Failed to save project: {result}")

    def _replace_browser_widget(self, new_browser_widget):
        try:
            browser_tab_index = 0
            browser_tab_widget = self.content_stack.widget(browser_tab_index)
            splitter = browser_tab_widget.findChild(QSplitter)
            if splitter:
                old_browser = splitter.widget(0)
                if old_browser and hasattr(old_browser, 'cleanup'):
                    try:
                        old_browser.cleanup()
                    except Exception:
                        pass
                splitter.insertWidget(0, new_browser_widget)
                if old_browser:
                    old_browser.hide()
                    QTimer.singleShot(100, old_browser.deleteLater)
            self.browser_widget = new_browser_widget
        except Exception as e:
            print(f"⚠️ [REPLACE BROWSER] Error: {e}")

    def on_open_project(self):
        current = self.project_list.currentItem()
        if not current:
            self.log("⚠️ No project selected")
            return
        
        project_name = current.text().replace("📂  ", "")
        
        print(f"\n{'='*70}")
        print(f"📂 [OPEN PROJECT] Загрузка проекта: {project_name}")
        print(f"{'='*70}")
        
        project_data, msg = self.project_manager.load_project(project_name)
        
        if project_data:
            from PySide6.QtWebEngineCore import QWebEngineProfile
            project_path = os.path.join(self.project_manager.projects_dir, project_name)
            profile_path = os.path.join(project_path, "profile")
            
            if not os.path.exists(profile_path):
                os.makedirs(profile_path)
            
            profile = QWebEngineProfile(project_name)
            profile.setPersistentStoragePath(profile_path)
            profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
            )
            
            print(f"   📁 Профиль загружен из: {profile_path}")
            print(f"   🍪 Политика: ForcePersistentCookies")
            print(f"{'='*70}\n")
            
            new_browser = BrowserWidget(profile)
            new_browser.url_changed.connect(self.on_browser_url_changed)
            new_browser.devtools_changed.connect(self.on_devtools_changed)
            new_browser.selector_captured.connect(self.on_selector_captured)
            
            browser_data = project_data.get('browser_data', {})
            tabs = browser_data.get('tabs', [])
            if tabs:
                new_browser.restore_tabs(tabs)
                self.log(f"   🌐 Restored {len(tabs)} browser tabs")
            else:
                new_browser.add_new_tab("https://google.com")
            
            self._replace_browser_widget(new_browser)
            
            if hasattr(self, 'vm_table'):
                self.vm_table.clear_all()
                for var in project_data.get('variables', []):
                    self.vm_table.add_variable(
                        name=var.get('name', ''),
                        xpath=var.get('xpath', ''),
                        var_type=var.get('type', 'Static'),
                        url=var.get('url', ''),
                        sample=var.get('sample', '')
                    )
                self.log(f"   📊 Loaded {len(project_data.get('variables', []))} variables")
            
            self.project_name.setText(project_name)
            self.project_created.setText(project_data['metadata'].get('created', '—')[:16])
            self.project_modified.setText(project_data['metadata'].get('modified', '—')[:16])
            self.project_vars_count.setText(str(len(project_data.get('variables', []))))
            
            preview_text = ""
            for var in project_data.get('variables', []):
                preview_text += f"• {var.get('name', '?')} → {var.get('xpath', '')[:50]}...\n"
            self.vars_preview.setText(preview_text if preview_text else "No variables")
            
            self.project_manager.current_project = project_name
            self.project_manager.current_profile = profile
            
            # Обновляем Script Editor
            if hasattr(self, 'script_editor'):
                self.script_editor.update_project(project_name)
            
        else:
            QMessageBox.warning(self, "Error", f"Failed to load project: {msg}")

    def on_export_parser(self):
        current = self.project_list.currentItem()
        if not current:
            self.log("⚠️ No project selected")
            QMessageBox.warning(self, "Warning", "Please select a project first!")
            return
        
        project_name = current.text().replace("📂  ", "")
        
        self.on_save_project()
        
        config_path = self.generate_parser_config(project_name)
        
        if config_path:
            self.log(f"✅ Parser config generated: {config_path}")
            QMessageBox.information(
                self, 
                "Success", 
                f"Parser config generated successfully!\n\n"
                f"Location: {config_path}\n\n"
                f"Use UPBParser to run:\n"
                f"https://github.com/c00lpython/UPBParser"
            )
        else:
            QMessageBox.warning(self, "Error", "Failed to generate parser config")

    def generate_parser_config(self, project_name: str):
        project_path = os.path.join(self.project_manager.projects_dir, project_name)
        config_path = os.path.join(project_path, "config.conf")
        
        variables = []
        if hasattr(self, 'vm_table'):
            for row in range(self.vm_table.table.rowCount()):
                name_item = self.vm_table.table.item(row, 0)
                xpath_item = self.vm_table.table.item(row, 1)
                type_combo = self.vm_table.table.cellWidget(row, 2)
                url_item = self.vm_table.table.item(row, 3)
                sample_item = self.vm_table.table.item(row, 4)
                
                if name_item and xpath_item and name_item.text():
                    var = {
                        "name": name_item.text(),
                        "selector": xpath_item.text(),
                        "strategy": "xpath",
                        "type": "text"
                    }
                    
                    if type_combo:
                        var_type = type_combo.currentText().lower()
                        if var_type == "dynamic":
                            var["type"] = "dynamic"
                        elif var_type == "network":
                            var["type"] = "network"
                            if url_item and url_item.text():
                                var["url"] = url_item.text()
                    
                    if sample_item and sample_item.text():
                        var["sample"] = sample_item.text()
                    
                    variables.append(var)
        
        current_url = "https://example.com"
        if hasattr(self, 'browser_widget'):
            current_tab = self.browser_widget.get_current_tab()
            if current_tab:
                current_url = current_tab.get_current_url()
        
        config_content = f"""[PROJECT]
name = {project_name}
url = {current_url}
description = Parser generated by UPB for {project_name}

[BROWSER]
headless = true
timeout = 10
wait_between_requests = 1
retry_count = 3

[URLS]
main = {current_url}
additional = []

[AUTH]
enabled = false
login_url = 
username = 
password = 

[VARIABLES]
items = {json.dumps(variables, indent=4, ensure_ascii=False)}

[OUTPUT]
format = excel
excel_path = output.xlsx
json_path = output.json

[LOGGING]
level = INFO
log_file = parser.log

[TELEGRAM]
enabled = false
bot_token = 
chat_id = 
"""
        
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        self.log(f"✅ Generated config.conf for project: {project_name}")
        self.log(f"   📊 Variables: {len(variables)}")
        self.log(f"   🌐 URL: {current_url}")
        return config_path

    def on_delete_project(self):
        current = self.project_list.currentItem()
        if not current:
            self.log("⚠️ No project selected")
            return
        
        project_name = current.text().replace("📂  ", "")
        
        if self.project_manager.current_project == project_name:
            if hasattr(self, 'browser_widget') and hasattr(self.browser_widget, 'cleanup'):
                self.browser_widget.cleanup()
            
            from PySide6.QtWebEngineCore import QWebEngineProfile
            temp_id = str(uuid.uuid4())[:8]
            temp_profile = QWebEngineProfile(f"Temporary_{temp_id}")
            temp_profile.setPersistentStoragePath(f"temp_profile_{temp_id}")
            temp_profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
            )
            
            new_browser = BrowserWidget(temp_profile)
            new_browser.url_changed.connect(self.on_browser_url_changed)
            new_browser.devtools_changed.connect(self.on_devtools_changed)
            new_browser.selector_captured.connect(self.on_selector_captured)
            
            self._replace_browser_widget(new_browser)
        
        import time
        time.sleep(0.5)
        
        reply = QMessageBox.question(
            self, "Delete Project", 
            f"Delete '{project_name}'?\n\nThis action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, result = self.project_manager.delete_project(project_name)
            if success:
                self.log(f"✅ Project deleted: {project_name}")
                self.refresh_project_list()
                
                self.project_name.clear()
                self.project_created.setText("—")
                self.project_modified.setText("—")
                self.project_vars_count.setText("0")
                self.vars_preview.clear()
                
                if hasattr(self, 'vm_table'):
                    self.vm_table.clear_all()
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete project: {result}")

    def create_vm_panel(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.vm_table = VmTable()
        self.vm_table.view_in_browser_requested.connect(self.view_variable_in_browser)
        layout.addWidget(self.vm_table)
        return widget

    def create_build_panel(self):
        from ui.build_widget import BuildWidget
        self.build_widget = BuildWidget(self)
        self.build_widget.log_signal.connect(self.log)
        return self.build_widget

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
    
    def on_build_clicked(self):
        self.log("🔨 Build started...")
        
        current = self.project_list.currentItem()
        if not current:
            self.log("⚠️ No project selected")
            QMessageBox.warning(self, "Warning", "Please select a project first!")
            return
        
        project_name = current.text().replace("📂  ", "")
        
        self.on_save_project()
        
        config_path = self.generate_parser_config(project_name)
        
        if config_path and os.path.exists(config_path):
            self.log(f"✅ Build completed! Config saved to: {config_path}")
            QMessageBox.information(
                self, 
                "Build Successful", 
                f"Parser configuration generated!\n\n"
                f"📁 Location: {config_path}\n\n"
                f"📊 Variables: {len(self.vm_table.get_all_variables())}\n\n"
                f"🔧 Next steps:\n"
                f"1. Clone UPBParser: https://github.com/c00lpython/UPBParser\n"
                f"2. Copy config.conf to UPBParser folder\n"
                f"3. Run: python main.py"
            )
        else:
            self.log("❌ Build failed")
            QMessageBox.warning(self, "Error", "Failed to generate parser config")
    
    def on_run_clicked(self):
        self.log("Running parser... (placeholder)")
        self.log("Parser execution completed.")
    
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
        
        tabs = [self.tab_browser, self.tab_project, self.tab_vm, self.tab_build, self.tab_test, self.tab_script]
        for i, tab in enumerate(tabs):
            if i == index:
                tab.setStyleSheet(tab_style_active)
            else:
                tab.setStyleSheet(tab_style_normal)
        
        tab_names = ["Browser", "Project", "VM", "Build", "Test", "Script Editor"]
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
        current_web_view = self.browser_widget.get_current_web_view()
        if current_web_view:
            current_web_view.page().runJavaScript(js)
    
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
        current_web_view = self.browser_widget.get_current_web_view()
        if current_web_view:
            current_web_view.page().runJavaScript(js)
    
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