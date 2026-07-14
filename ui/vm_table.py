# ui/vm_table.py
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QComboBox, QWidget, 
    QVBoxLayout, QHBoxLayout, QPushButton, QHeaderView,
    QLineEdit, QMenu, QApplication
)
from PySide6.QtCore import Qt, Signal
import re


class VmTable(QWidget):
    # Сигнал для открытия в браузере
    view_in_browser_requested = Signal(str, str)  # url, xpath
    
    def __init__(self):
        super().__init__()
        
        # ========== КОСМИЧЕСКИЙ ГРАДИЕНТНЫЙ ФОН ==========
        self.setStyleSheet("""
            QWidget#VmTable {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #0a0a1a,
                    stop:0.3 #14142e,
                    stop:0.6 #1a0a2e,
                    stop:1 #0a0a2a);
                border-radius: 24px;
                border: 1px solid rgba(255, 255, 255, 0.06);
            }
        """)
        self.setObjectName("VmTable")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # ========== ПАНЕЛЬ ПОИСКА ==========
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search variables...")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.04);
                color: #e8e8f0;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 8px 14px;
                font-size: 12px;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit:focus {
                border: 1px solid rgba(124, 77, 255, 0.4);
                background-color: rgba(255, 255, 255, 0.06);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.3);
            }
        """)
        
        self.search_column = QComboBox()
        self.search_column.addItems(["All", "Name", "XPath/CSS", "Type", "URL", "Sample Text"])
        self.search_column.setCurrentText("All")
        self.search_column.setStyleSheet("""
            QComboBox {
                background-color: rgba(255, 255, 255, 0.04);
                color: #e8e8f0;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 8px 14px;
                font-size: 12px;
                min-width: 100px;
                font-family: 'Segoe UI', sans-serif;
            }
            QComboBox:hover {
                border-color: rgba(255, 255, 255, 0.15);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMiIgaGVpZ2h0PSI4IiB2aWV3Qm94PSIwIDAgMTIgOCI+PHBhdGggZD0iTTEgMWw1IDUgNS01IiBzdHJva2U9InJnYmEoMjU1LDI1NSwyNTUsMC41KSIgc3Ryb2tlLXdpZHRoPSIyIiBmaWxsPSJub25lIi8+PC9zdmc+);
                width: 12px;
                height: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a2e;
                color: #e8e8f0;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                selection-background-color: rgba(124, 77, 255, 0.25);
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border-radius: 8px;
            }
            QComboBox QAbstractItemView::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(124, 77, 255, 0.3),
                    stop:1 rgba(74, 122, 255, 0.3));
                color: white;
            }
        """)
        
        self.btn_clear_search = QPushButton("✕")
        self.btn_clear_search.setMaximumWidth(32)
        self.btn_clear_search.clicked.connect(self.clear_search)
        self.btn_clear_search.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.04);
                color: rgba(255, 255, 255, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 12px;
                padding: 6px;
                font-size: 12px;
                font-weight: 300;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
                color: rgba(255, 255, 255, 0.8);
                border-color: rgba(255, 255, 255, 0.15);
            }
        """)
        
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.search_column)
        search_layout.addWidget(self.btn_clear_search)
        
        # ========== КНОПКИ УПРАВЛЕНИЯ ==========
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        self.btn_add = QPushButton("➕ Add Variable")
        self.btn_remove = QPushButton("❌ Remove Selected")
        self.btn_clear = QPushButton("🗑 Clear All")
        
        btn_style = """
            QPushButton {
                background-color: rgba(255, 255, 255, 0.04);
                color: #e8e8f0;
                padding: 8px 16px;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 12px;
                font-size: 12px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.08);
                color: #ffffff;
                border-color: rgba(255, 255, 255, 0.15);
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.02);
            }
        """
        
        self.btn_add.setStyleSheet(btn_style)
        self.btn_remove.setStyleSheet(btn_style)
        self.btn_clear.setStyleSheet(btn_style)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()
        
        # ========== ТАБЛИЦА - КАРТОЧКА ==========
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "XPath/CSS", "Type", "URL", "Sample Text"])
        
        self.table.setStyleSheet("""
            /* ----- КАРТОЧКА ТАБЛИЦЫ ----- */
            QTableWidget {
                background-color: rgba(10, 10, 26, 0.6);
                color: rgba(255, 255, 255, 0.5);
                gridline-color: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 20px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
                outline: none;
                selection-background-color: transparent;
                padding: 4px;
            }
            
            /* ----- ЯЧЕЙКИ ----- */
            QTableWidget::item {
                padding: 8px 14px;
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.03);
                background-color: transparent;
                color: rgba(255, 255, 255, 0.5);
            }
            
            /* ----- ВЫДЕЛЕННАЯ СТРОКА (как focus-within) ----- */
            QTableWidget::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(124, 77, 255, 0.15),
                    stop:1 rgba(74, 122, 255, 0.15));
                color: #ffffff;
                border-left: 3px solid qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9b59b6,
                    stop:1 #7c4dff);
            }
            
            /* ----- ПРИ НАВЕДЕНИИ НА ЯЧЕЙКУ ----- */
            QTableWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.04);
                color: rgba(255, 255, 255, 0.8);
            }
            
            /* ----- ЗАГОЛОВКИ (thead) ----- */
            QHeaderView::section {
                background-color: rgba(255, 255, 255, 0.03);
                color: rgba(255, 255, 255, 0.5);
                padding: 10px 14px;
                border: none;
                border-bottom: 2px solid qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(155, 89, 182, 0.2),
                    stop:1 rgba(124, 77, 255, 0.2));
                font-weight: 600;
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                text-align: left;
                font-family: 'Segoe UI', sans-serif;
            }
            
            QHeaderView::section:hover {
                background-color: rgba(255, 255, 255, 0.06);
                color: rgba(255, 255, 255, 0.8);
            }
            
            /* ----- СКРОЛЛБАРЫ (космические) ----- */
            QScrollBar:vertical {
                background-color: rgba(255, 255, 255, 0.02);
                width: 6px;
                border-radius: 3px;
                margin: 4px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(155, 89, 182, 0.3),
                    stop:1 rgba(74, 122, 255, 0.3));
                border-radius: 3px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(155, 89, 182, 0.5),
                    stop:1 rgba(74, 122, 255, 0.5));
            }
            QScrollBar:horizontal {
                background-color: rgba(255, 255, 255, 0.02);
                height: 6px;
                border-radius: 3px;
                margin: 4px;
            }
            QScrollBar::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(155, 89, 182, 0.3),
                    stop:1 rgba(74, 122, 255, 0.3));
                border-radius: 3px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(155, 89, 182, 0.5),
                    stop:1 rgba(74, 122, 255, 0.5));
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                height: 0px;
                width: 0px;
            }
        """)
        
        # Настройки таблицы
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        
        # Растягиваем колонки
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(True)
        
        # Сборка
        layout.addLayout(search_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)
        
        # Подключаем сигналы
        self.btn_add.clicked.connect(self.add_empty_variable)
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_clear.clicked.connect(self.clear_all)
    
    def _show_context_menu(self, pos):
        """Показывает контекстное меню для выбранной строки"""
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        
        self.table.selectRow(row)
        
        name_item = self.table.item(row, 0)
        xpath_item = self.table.item(row, 1)
        type_combo = self.table.cellWidget(row, 2)
        url_item = self.table.item(row, 3)
        sample_item = self.table.item(row, 4)
        
        var_name = name_item.text().strip() if name_item else ""
        xpath = xpath_item.text().strip() if xpath_item else ""
        var_type = type_combo.currentText() if type_combo else "Static"
        url = url_item.text().strip() if url_item else ""
        sample = sample_item.text().strip() if sample_item else ""
        
        if not var_name:
            return
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(20, 20, 40, 0.95);
                color: #e8e8f0;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 16px;
                padding: 6px;
                font-size: 12px;
                font-family: 'Segoe UI', sans-serif;
            }
            QMenu::item {
                padding: 8px 24px;
                border-radius: 8px;
                margin: 2px 4px;
            }
            QMenu::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(155, 89, 182, 0.2),
                    stop:1 rgba(124, 77, 255, 0.2));
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 0.04);
                margin: 4px 8px;
            }
        """)
        
        header = menu.addAction(f"📦 {var_name}")
        header.setEnabled(False)
        
        type_action = menu.addAction(f"📌 Type: {var_type}")
        type_action.setEnabled(False)
        
        menu.addSeparator()
        
        if url:
            view_action = menu.addAction("🌐 View in Browser")
            view_action.setToolTip(f"Open {url} and highlight element by XPath")
            view_action.triggered.connect(
                lambda checked=False, u=url, x=xpath: self.view_in_browser_requested.emit(u, x)
            )
        else:
            no_url = menu.addAction("🌐 View in Browser (no URL)")
            no_url.setEnabled(False)
        
        menu.addSeparator()
        
        copy_menu = menu.addMenu("📋 Copy")
        copy_menu.setStyleSheet(menu.styleSheet())
        
        copy_name = copy_menu.addAction("Copy Name")
        copy_name.triggered.connect(lambda: QApplication.clipboard().setText(var_name))
        
        if xpath:
            copy_xpath = copy_menu.addAction("Copy XPath")
            copy_xpath.triggered.connect(lambda: QApplication.clipboard().setText(xpath))
        
        if url:
            copy_url = copy_menu.addAction("Copy URL")
            copy_url.triggered.connect(lambda: QApplication.clipboard().setText(url))
        
        if sample:
            copy_sample = copy_menu.addAction("Copy Sample")
            copy_sample.triggered.connect(lambda: QApplication.clipboard().setText(sample))
        
        copy_all = copy_menu.addAction("Copy All")
        copy_all.triggered.connect(
            lambda: QApplication.clipboard().setText(
                f"Name: {var_name}\nXPath: {xpath}\nType: {var_type}\nURL: {url}\nSample: {sample}"
            )
        )
        
        menu.addSeparator()
        
        delete_action = menu.addAction("🗑 Delete Variable")
        delete_action.triggered.connect(lambda: self._delete_row(row))
        
        menu.exec(self.table.viewport().mapToGlobal(pos))
    
    def _delete_row(self, row: int):
        if 0 <= row < self.table.rowCount():
            self.table.removeRow(row)
    
    def filter_table(self):
        search_text = self.search_input.text().lower()
        search_column = self.search_column.currentText()
        
        if not search_text:
            for i in range(self.table.rowCount()):
                self.table.setRowHidden(i, False)
            return
        
        for row in range(self.table.rowCount()):
            show_row = False
            
            if search_column == "All" or search_column == "Name":
                name_item = self.table.item(row, 0)
                if name_item and search_text in name_item.text().lower():
                    show_row = True
            
            if not show_row and (search_column == "All" or search_column == "XPath/CSS"):
                xpath_item = self.table.item(row, 1)
                if xpath_item and search_text in xpath_item.text().lower():
                    show_row = True
            
            if not show_row and (search_column == "All" or search_column == "Type"):
                combo = self.table.cellWidget(row, 2)
                if combo and search_text in combo.currentText().lower():
                    show_row = True
            
            if not show_row and (search_column == "All" or search_column == "URL"):
                url_item = self.table.item(row, 3)
                if url_item and search_text in url_item.text().lower():
                    show_row = True
            
            if not show_row and (search_column == "All" or search_column == "Sample Text"):
                sample_item = self.table.item(row, 4)
                if sample_item and search_text in sample_item.text().lower():
                    show_row = True
            
            self.table.setRowHidden(row, not show_row)
    
    def clear_search(self):
        self.search_input.clear()
    
    def add_variable(self, name: str = "", xpath: str = "", var_type: str = "Static", url: str = "", sample: str = ""):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        # Name
        name_item = QTableWidgetItem(name)
        name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, name_item)
        
        # XPath
        xpath_item = QTableWidgetItem(xpath)
        xpath_item.setFlags(xpath_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 1, xpath_item)
        
        # Type (ComboBox)
        combo = QComboBox()
        combo.addItems(["Static", "Dynamic", "Network"])
        combo.setCurrentText(var_type)
        combo.setStyleSheet("""
            QComboBox {
                background-color: transparent;
                color: #e8e8f0;
                border: none;
                padding: 4px 8px;
                font-size: 12px;
                font-family: 'Segoe UI', sans-serif;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a2e;
                color: #e8e8f0;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 12px;
                selection-background-color: rgba(124, 77, 255, 0.25);
            }
            QComboBox QAbstractItemView::item:selected {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(155, 89, 182, 0.3),
                    stop:1 rgba(124, 77, 255, 0.3));
                color: white;
            }
        """)
        self.table.setCellWidget(row, 2, combo)
        
        # URL
        url_item = QTableWidgetItem(url)
        url_item.setFlags(url_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 3, url_item)
        
        # Sample Text
        sample_item = QTableWidgetItem(sample)
        sample_item.setFlags(sample_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 4, sample_item)
        
        self.table.scrollToBottom()
    
    def add_empty_variable(self):
        self.add_variable("new_var", "", "Static", "", "")
    
    def remove_selected(self):
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        for row in sorted(selected_rows, reverse=True):
            self.table.removeRow(row)
    
    def clear_all(self):
        self.table.setRowCount(0)
    
    def get_all_variables(self):
        variables = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            xpath_item = self.table.item(row, 1)
            combo = self.table.cellWidget(row, 2)
            url_item = self.table.item(row, 3)
            sample_item = self.table.item(row, 4)
            
            variables.append({
                'name': name_item.text() if name_item else "",
                'xpath': xpath_item.text() if xpath_item else "",
                'type': combo.currentText() if combo else "Static",
                'url': url_item.text() if url_item else "",
                'sample': sample_item.text() if sample_item else ""
            })
        return variables
    
    def import_from_select(self, url: str, xpath: str, text: str, tag: str, alt: str = ""):
        if text and text.strip():
            base_name = text.strip()[:30]
        elif tag.upper() == "IMG" and alt and alt.strip():
            base_name = alt.strip()[:30]
        else:
            base_name = "empty"
        
        base_name = re.sub(r'[^a-zA-Z0-9_а-яА-ЯёЁ\s-]', '', base_name)
        base_name = base_name.replace(' ', '_')
        
        if not base_name:
            base_name = "empty"
        
        existing_names = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            if name_item:
                existing_names.append(name_item.text())
        
        final_name = base_name
        counter = 1
        while final_name in existing_names:
            counter += 1
            final_name = f"{base_name}_{counter}"
        
        self.add_variable(
            name=final_name,
            xpath=xpath,
            var_type="Static",
            url=url,
            sample=text[:50] if text else (alt[:50] if alt else "")
        )
        
        return final_name