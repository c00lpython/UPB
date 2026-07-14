# ui/main_window.py
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFrame, QLabel, QPushButton, QTextEdit,
    QStackedWidget, QListWidget, QListWidgetItem, QLineEdit,
    QGroupBox, QGridLayout, QMessageBox, QInputDialog,QSizePolicy
)
from PySide6.QtCore import Qt, QDateTime, QUrl, QTimer, Signal
from PySide6.QtGui import QKeyEvent, QPixmap, QPainter, QColor, QBrush, QPen, QCursor
from ui.browser_widget import BrowserWidget
from ui.vm_table import VmTable
from ui.SE.script_editor import ScriptEditor
from core.project_manager import ProjectManager

import os
import json
import uuid
import sys
import psutil
from datetime import datetime


class MainWindow(QMainWindow):
    about_to_close = Signal()

    def __init__(self, profile=None):
        super().__init__()
        self.setWindowTitle("UPB - Universal Parser Builder")
        self.setGeometry(100, 100, 1400, 900)
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.drag_pos = None
        
        self.profile = profile
        self.project_manager = ProjectManager()
        
        os.environ['QTWEBENGINE_REMOTE_DEBUGGING'] = '9222'
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.create_top_bar()
        main_layout.addWidget(self.top_bar)
        
        # ========== СНАЧАЛА СОЗДАЁМ ВСЕ ПАНЕЛИ ==========
        # Создаём content_stack с вкладками
        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(self.create_browser_view())
        self.content_stack.addWidget(self.create_project_panel())
        self.content_stack.addWidget(self.create_vm_panel())
        self.content_stack.addWidget(self.create_build_panel())
        self.content_stack.addWidget(self.create_test_panel())
        self.content_stack.addWidget(self.create_script_editor_panel())
        
        # Создаём нижнюю панель
        self.create_bottom_panel()
        
        # ========== ТЕПЕРЬ СОЗДАЁМ СПЛИТТЕР ==========
        self.main_splitter = QSplitter(Qt.Orientation.Vertical)
        self.main_splitter.setHandleWidth(4)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: rgba(255, 255, 255, 0.08);
                height: 4px;
            }
            QSplitter::handle:hover {
                background-color: rgba(74, 122, 255, 0.4);
                height: 4px;
            }
            QSplitter::handle:pressed {
                background-color: rgba(74, 122, 255, 0.6);
            }
        """)
        
        # Добавляем виджеты в сплиттер
        self.main_splitter.addWidget(self.content_stack)
        self.main_splitter.addWidget(self.bottom_frame)
        
        # Устанавливаем начальные размеры
        self.main_splitter.setSizes([700, 250])
        
        # Отладка
        print(f"🔍 [SPLITTER DEBUG] Main splitter created")
        print(f"   Children collapsible: {self.main_splitter.childrenCollapsible()}")
        print(f"   Handle width: {self.main_splitter.handleWidth()}")
        print(f"   Initial sizes: {self.main_splitter.sizes()}")
        
        # Подключаем сигнал для отслеживания
        self.main_splitter.splitterMoved.connect(
            lambda pos, idx: print(f"🔍 [SPLITTER MOVED] Position: {pos}, Index: {idx}, Sizes: {self.main_splitter.sizes()}")
        )
        
        main_layout.addWidget(self.main_splitter, 1)
        
        self._browser_ready = False
        QTimer.singleShot(500, self._set_browser_ready)
        QTimer.singleShot(2000, self.auto_open_latest_project)
        
        # Таймер для статистики
        self.start_time = datetime.now()
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_system_stats)
        self.stats_timer.start(2000)
        
        self.log("🚀 UPB v2.0 Ready")
        self.log("💡 Select mode: OFF (Press Ctrl+Shift+C to toggle)")

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
                        document.querySelectorAll('.upb-overlay, .upb-corner, .upb-label, .upb-margin, .upb-padding').forEach(el => el.remove());
                        
                        let xpath = "{safe_xpath}";
                        let result = document.evaluate(xpath, document, null, 
                            XPathResult.FIRST_ORDERED_NODE_TYPE, null);
                        let element = result.singleNodeValue;
                        
                        if (!element) {{
                            console.log('%c❌ UPB: Element not found', 'color: #ff0000; font-weight: bold;');
                            return '❌ Element not found';
                        }}
                        
                        element.scrollIntoView({{behavior: 'smooth', block: 'center', inline: 'center'}});
                        
                        let rect = element.getBoundingClientRect();
                        let top = rect.top + window.scrollY;
                        let left = rect.left + window.scrollX;
                        let width = rect.width;
                        let height = rect.height;
                        
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
                        
                        createCorner(left - 6, top - 6, 0);
                        createCorner(left + width - 6, top - 6, 90);
                        createCorner(left + width - 6, top + height - 6, 180);
                        createCorner(left - 6, top + height - 6, 270);
                        
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
                        
                        document.addEventListener('click', function cleanup(e) {{
                            document.querySelectorAll('.upb-overlay, .upb-corner, .upb-label').forEach(el => el.remove());
                            document.removeEventListener('click', cleanup);
                            clearInterval(pulseInterval);
                        }}, {{once: true}});
                        
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
        self.top_bar.setMaximumHeight(44)
        self.top_bar.setProperty("topbar", True)
        
        layout = QHBoxLayout(self.top_bar)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(20)
        
        logo_container = QWidget()
        logo_container.setFixedSize(32, 32)
        logo_container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #9b59b6,
                    stop:0.5 #8e44ad,
                    stop:1 #7c4dff);
                border-radius: 6px;
            }
        """)
        
        logo_label = QLabel("UPB", logo_container)
        logo_label.setGeometry(0, 0, 32, 32)
        logo_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: 800;
                font-size: 9px;
                letter-spacing: 0.5px;
                qproperty-alignment: AlignCenter;
                font-family: 'Segoe UI', sans-serif;
            }
        """)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_container)
        
        version_label = QLabel("v2.0")
        version_label.setStyleSheet("""
            color: #ffffff;
            font-weight: 300;
            font-size: 10px;
            letter-spacing: 0.5px;
            opacity: 0.7;
            padding-top: 4px;
        """)
        version_label.setProperty("version", True)
        layout.addWidget(version_label)
        
        separator = QLabel("│")
        separator.setProperty("separator", True)
        layout.addWidget(separator)
        
        self.tab_browser = QPushButton("Browser")
        self.tab_project = QPushButton("Project")
        self.tab_vm = QPushButton("VM")
        self.tab_build = QPushButton("Build")
        self.tab_test = QPushButton("Test")
        self.tab_script = QPushButton("Script Editor")
        
        for tab in [self.tab_browser, self.tab_project, self.tab_vm, 
                    self.tab_build, self.tab_test, self.tab_script]:
            tab.setProperty("tab", True)
            layout.addWidget(tab)
        
        layout.addStretch()
        
        self.btn_min = QPushButton("—")
        self.btn_max = QPushButton("□")
        self.btn_close = QPushButton("✕")
        
        self.btn_min.setProperty("windowbtn", True)
        self.btn_max.setProperty("windowbtn", True)
        self.btn_close.setProperty("windowbtn", True)
        self.btn_close.setProperty("closebtn", True)
        
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
        
        self.tab_browser.setProperty("active", True)
        self.current_tab_index = 0
    
    def create_browser_view(self):
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        from PySide6.QtWebEngineCore import QWebEngineProfile
        
        if self.project_manager and self.project_manager.current_project:
            project_path = os.path.join(self.project_manager.projects_dir, self.project_manager.current_project)
            profile_path = os.path.join(project_path, "profile")
            
            os.makedirs(profile_path, exist_ok=True)
            
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
        
        self.browser_widget = BrowserWidget(profile)
        
        self.browser_widget.url_changed.connect(self.on_browser_url_changed)
        self.browser_widget.devtools_changed.connect(self.on_devtools_changed)
        self.browser_widget.selector_captured.connect(self.on_selector_captured)
        
        self.devtools_container = QWidget()
        self.devtools_container.setProperty("devtools_container", True)
        self.devtools_container_layout = QVBoxLayout(self.devtools_container)
        self.devtools_container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.current_devtools_view = None
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.browser_widget)
        splitter.addWidget(self.devtools_container)
        splitter.setSizes([850, 150])
        splitter.setHandleWidth(4)
        splitter.setProperty("browser_splitter", True)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: rgba(255, 255, 255, 0.05);
                width: 4px;
            }
            QSplitter::handle:hover {
                background-color: rgba(74, 122, 255, 0.3);
                width: 4px;
            }
            QSplitter::handle:pressed {
                background-color: rgba(74, 122, 255, 0.5);
            }
        """)
        
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
        projects_label.setProperty("header", True)
        left_layout.addWidget(projects_label)
        
        self.project_list = QListWidget()
        self.project_list.setProperty("project_list", True)
        
        self.refresh_project_list()
        left_layout.addWidget(self.project_list)
        
        self.btn_new_project = QPushButton("➕ New Project")
        self.btn_new_project.setProperty("primary", True)
        left_layout.addWidget(self.btn_new_project)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)
        
        info_group = QGroupBox("📄 Project Details")
        info_group.setProperty("project_details", True)
        
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(10)
        
        info_layout.addWidget(QLabel("Name:"), 0, 0)
        self.project_name = QLineEdit()
        self.project_name.setPlaceholderText("Project name")
        self.project_name.setReadOnly(True)
        info_layout.addWidget(self.project_name, 0, 1)
        
        info_layout.addWidget(QLabel("Created:"), 1, 0)
        self.project_created = QLabel("—")
        info_layout.addWidget(self.project_created, 1, 1)
        
        info_layout.addWidget(QLabel("Modified:"), 2, 0)
        self.project_modified = QLabel("—")
        info_layout.addWidget(self.project_modified, 2, 1)
        
        info_layout.addWidget(QLabel("Variables:"), 3, 0)
        self.project_vars_count = QLabel("0")
        self.project_vars_count.setProperty("accent", True)
        info_layout.addWidget(self.project_vars_count, 3, 1)
        
        right_layout.addWidget(info_group)
        
        vars_group = QGroupBox("📊 Variables Preview")
        vars_group.setProperty("variables_preview", True)
        
        vars_layout = QVBoxLayout(vars_group)
        self.vars_preview = QTextEdit()
        self.vars_preview.setReadOnly(True)
        self.vars_preview.setMaximumHeight(150)
        self.vars_preview.setProperty("preview", True)
        vars_layout.addWidget(self.vars_preview)
        
        right_layout.addWidget(vars_group)
        
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        
        self.btn_open = QPushButton("📂 Open Project")
        self.btn_save = QPushButton("💾 Save Project")
        self.btn_export = QPushButton("🚀 Export Parser")
        self.btn_delete = QPushButton("🗑 Delete")
        self.btn_delete.setProperty("danger", True)
        
        for btn in [self.btn_open, self.btn_save, self.btn_export, self.btn_delete]:
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
        label.setProperty("test_label", True)
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(label)
        return widget
        
    def create_bottom_panel(self):
        """Создаёт нижнюю панель с консолью и кнопками"""
        bottom_widget = QWidget()
        bottom_widget.setProperty("bottom_frame", True)
        
        # ВАЖНО: Устанавливаем политику размера
        bottom_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # Горизонтально - расширяется
            QSizePolicy.Policy.Expanding   # Вертикально - расширяется (ключевое!)
        )
        # Убираем все ограничения размеров
        bottom_widget.setMinimumSize(0, 50)  # Минимальная высота 50px
        bottom_widget.setMaximumSize(16777215, 16777215)  # Без максимальных ограничений
        
        bottom_layout = QHBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(5, 2, 5, 2)
        bottom_layout.setSpacing(10)
        
        # ========== КОНСОЛЬ ==========
        console_container = QWidget()
        console_container.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        
        console_layout = QVBoxLayout(console_container)
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_layout.setSpacing(2)
        
        # Статусная строка (фиксированная высота)
        status_widget = QWidget()
        status_widget.setFixedHeight(20)
        status_layout = QHBoxLayout(status_widget)
        status_layout.setSpacing(15)
        status_layout.setContentsMargins(2, 0, 2, 0)
        
        self.console_label = QLabel("v2.0 | console: Ready")
        self.console_label.setProperty("console_label", True)
        status_layout.addWidget(self.console_label)
        
        sep = QLabel("•")
        sep.setStyleSheet("color: rgba(255,255,255,0.2); font-size: 12px;")
        status_layout.addWidget(sep)
        
        self.cpu_label = QLabel("💻 CPU: --%")
        self.cpu_label.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 10px; font-family: 'Consolas', monospace;")
        status_layout.addWidget(self.cpu_label)
        
        self.ram_label = QLabel("🧠 RAM: --/--MB")
        self.ram_label.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 10px; font-family: 'Consolas', monospace;")
        status_layout.addWidget(self.ram_label)
        
        self.uptime_label = QLabel("⏱️ Uptime: 00:00:00")
        self.uptime_label.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 10px; font-family: 'Consolas', monospace;")
        status_layout.addWidget(self.uptime_label)
        
        self.projects_label = QLabel("📁 Projects: 0")
        self.projects_label.setStyleSheet("color: rgba(255,255,255,0.5); font-size: 10px; font-family: 'Consolas', monospace;")
        status_layout.addWidget(self.projects_label)
        
        status_layout.addStretch()
        console_layout.addWidget(status_widget)
        
        # Консольный текст (растягивается)
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setProperty("console", True)
        self.console_text.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.console_text.setMinimumHeight(30)
        self.console_text.setMaximumHeight(16777215)
        
        console_layout.addWidget(self.console_text, 1)  # Stretch factor = 1
        
        # ========== КНОПКИ ==========
        tools_widget = QWidget()
        tools_widget.setFixedWidth(300)
        tools_widget.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Expanding
        )
        
        tools_layout = QHBoxLayout(tools_widget)
        tools_layout.setSpacing(10)
        tools_layout.setContentsMargins(5, 0, 5, 0)
        tools_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.btn_select = QPushButton("Select")
        self.btn_select.setCheckable(True)
        self.btn_select.setProperty("selectable", True)
        self.btn_select.setMinimumWidth(85)
        self.btn_select.setFixedHeight(35)
        
        self.btn_build = QPushButton("Build")
        self.btn_build.setProperty("success", True)
        self.btn_build.setMinimumWidth(85)
        self.btn_build.setFixedHeight(35)
        
        self.btn_run = QPushButton("Run")
        self.btn_run.setProperty("primary", True)
        self.btn_run.setMinimumWidth(85)
        self.btn_run.setFixedHeight(35)
        
        tools_layout.addWidget(self.btn_select)
        tools_layout.addWidget(self.btn_build)
        tools_layout.addWidget(self.btn_run)
        tools_layout.addStretch()
        
        bottom_layout.addWidget(console_container, 1)
        bottom_layout.addWidget(tools_widget)
        
        self.bottom_frame = bottom_widget
        
        self.btn_select.clicked.connect(self.toggle_select_mode)
        self.btn_build.clicked.connect(self.on_build_clicked)
        self.btn_run.clicked.connect(self.on_run_clicked)

    def update_system_stats(self):
        """Обновляет системную статистику"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            self.cpu_label.setText(f"💻 CPU: {cpu_percent:.0f}%")
            
            mem = psutil.virtual_memory()
            used_mb = mem.used / (1024 * 1024)
            total_mb = mem.total / (1024 * 1024)
            self.ram_label.setText(f"🧠 RAM: {used_mb:.0f}/{total_mb:.0f}MB")
            
            elapsed = datetime.now() - self.start_time
            hours = elapsed.seconds // 3600
            minutes = (elapsed.seconds % 3600) // 60
            seconds = elapsed.seconds % 60
            self.uptime_label.setText(f"⏱️ Uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            if hasattr(self, 'project_manager'):
                projects = self.project_manager.get_all_projects()
                self.projects_label.setText(f"📁 Projects: {len(projects)}")
                
        except ImportError:
            self.cpu_label.setText("💻 CPU: N/A")
            self.ram_label.setText("🧠 RAM: N/A")
            self.uptime_label.setText("⏱️ Uptime: N/A")
        except Exception:
            pass

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
        
        tabs = [self.tab_browser, self.tab_project, self.tab_vm, 
                self.tab_build, self.tab_test, self.tab_script]
        
        for i, tab in enumerate(tabs):
            if i == index:
                tab.setProperty("active", True)
            else:
                tab.setProperty("active", False)
            tab.style().unpolish(tab)
            tab.style().polish(tab)
        
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

    def closeEvent(self, event):
        """Корректное завершение приложения"""
        print("\n🛑 Closing application...")
        
        if hasattr(self, 'stats_timer'):
            self.stats_timer.stop()
        
        if hasattr(self, 'build_widget') and hasattr(self.build_widget, 'timer'):
            self.build_widget.timer.stop()
        
        if hasattr(self, 'browser_widget') and hasattr(self.browser_widget, 'cleanup'):
            try:
                self.browser_widget.cleanup()
                print("✅ Browser cleaned up")
            except Exception as e:
                print(f"⚠️ Browser cleanup error: {e}")
        
        if hasattr(self, 'script_editor') and hasattr(self.script_editor, 'canvas'):
            try:
                self.script_editor.canvas.stop_updates()
                print("✅ Script Editor stopped")
            except Exception as e:
                print(f"⚠️ Script Editor stop error: {e}")
        
        if hasattr(self, 'vm_table') and hasattr(self.vm_table, 'table'):
            try:
                self.vm_table.clear_all()
                print("✅ VM Table cleared")
            except Exception as e:
                print(f"⚠️ VM Table clear error: {e}")
        
        if self.project_manager and self.project_manager.current_project:
            try:
                self.on_save_project()
                print(f"✅ Project saved: {self.project_manager.current_project}")
            except Exception as e:
                print(f"⚠️ Project save error: {e}")
        
        event.accept()
        print("👋 Application closed successfully")
        
        QTimer.singleShot(100, lambda: sys.exit(0))