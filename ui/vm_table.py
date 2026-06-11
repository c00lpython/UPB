from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QComboBox, QWidget, 
    QVBoxLayout, QHBoxLayout, QPushButton, QHeaderView,
    QLineEdit, QMenu, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
import re


class VmTable(QWidget):
    # Сигнал для открытия в браузере
    view_in_browser_requested = pyqtSignal(str, str)  # url, xpath
    
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # ========== ПАНЕЛЬ ПОИСКА ==========
        search_layout = QHBoxLayout()
        search_layout.setSpacing(5)
        
        # Поле поиска
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search variables...")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                padding: 5px;
                border-radius: 3px;
            }
            QLineEdit:focus {
                border: 1px solid #0e639c;
            }
        """)
        
        # Выпадающий список для выбора колонки поиска
        self.search_column = QComboBox()
        self.search_column.addItems(["All", "Name", "XPath/CSS", "Type", "URL", "Sample Text"])
        self.search_column.setCurrentText("All")
        self.search_column.setStyleSheet("""
            QComboBox {
                background-color: #3c3c3c;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                padding: 5px;
                border-radius: 3px;
                min-width: 100px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                color: #cccccc;
                selection-background-color: #0e639c;
            }
        """)
        
        # Кнопка очистки поиска
        self.btn_clear_search = QPushButton("✕")
        self.btn_clear_search.setMaximumWidth(30)
        self.btn_clear_search.clicked.connect(self.clear_search)
        self.btn_clear_search.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                color: #cccccc;
                border: 1px solid #3c3c3c;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
                color: #cccccc;
            }
        """)
        
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.search_column)
        search_layout.addWidget(self.btn_clear_search)
        
        # ========== КНОПКИ УПРАВЛЕНИЯ ==========
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Add Variable")
        self.btn_remove = QPushButton("❌ Remove Selected")
        self.btn_clear = QPushButton("🗑 Clear All")
        
        btn_style = """
            QPushButton {
                background-color: #3c3c3c;
                color: #cccccc;
                padding: 5px 10px;
                border: none;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
                color: #cccccc;
            }
        """
        
        self.btn_add.setStyleSheet(btn_style)
        self.btn_remove.setStyleSheet(btn_style)
        self.btn_clear.setStyleSheet(btn_style)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()
        
        # ========== ТАБЛИЦА ==========
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "XPath/CSS", "Type", "URL", "Sample Text"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Включаем контекстное меню
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Отключаем вертикальную колонку с номерами строк
        self.table.verticalHeader().setVisible(False)
        
        # Отключаем чередование цветов (зебру)
        self.table.setAlternatingRowColors(False)
        
        # Единый стиль для всей таблицы
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d2d;
                gridline-color: #3c3c3c;
                border: none;
            }
            QTableWidget::item {
                color: #cccccc;
                background-color: #2d2d2d;
                padding: 5px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #0e639c;
            }
            QHeaderView::section {
                background-color: #252526;
                color: #cccccc;
                padding: 5px;
                border: none;
                border-right: 1px solid #3c3c3c;
                border-bottom: 1px solid #3c3c3c;
            }
            QTableCornerButton::section {
                background-color: #252526;
                border: none;
            }
        """)
        
        # Убираем сетку
        self.table.setShowGrid(False)
        
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
        # Получаем строку по позиции клика
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        
        # Выделяем строку
        self.table.selectRow(row)
        
        # Получаем данные из строки
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
        
        # Создаём контекстное меню
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                color: #cccccc;
                border: 1px solid #3d5afe;
                border-radius: 6px;
                padding: 4px;
                font-size: 12px;
            }
            QMenu::item {
                padding: 8px 30px 8px 12px;
                border-radius: 4px;
                margin: 2px 4px;
            }
            QMenu::item:selected {
                background-color: #094771;
                color: #ffffff;
            }
            QMenu::item:disabled {
                color: #666666;
            }
            QMenu::separator {
                height: 1px;
                background: #444;
                margin: 4px 8px;
            }
        """)
        
        # Заголовок с именем переменной
        header = menu.addAction(f"📦 {var_name}")
        header.setEnabled(False)
        
        # Тип переменной
        type_action = menu.addAction(f"📌 Type: {var_type}")
        type_action.setEnabled(False)
        
        menu.addSeparator()
        
        # View in Browser (только если есть URL)
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
        
        # Копирование данных
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
        
        # Удаление
        delete_action = menu.addAction("🗑 Delete Variable")
        delete_action.triggered.connect(lambda: self._delete_row(row))
        
        # Показываем меню
        menu.exec(self.table.viewport().mapToGlobal(pos))
    
    def _delete_row(self, row: int):
        """Удаляет строку по индексу"""
        if 0 <= row < self.table.rowCount():
            self.table.removeRow(row)
    
    def filter_table(self):
        """Фильтрует таблицу по поисковому запросу"""
        search_text = self.search_input.text().lower()
        search_column = self.search_column.currentText()
        
        if not search_text:
            # Показываем все строки
            for i in range(self.table.rowCount()):
                self.table.setRowHidden(i, False)
            return
        
        # Проходим по всем строкам
        for row in range(self.table.rowCount()):
            show_row = False
            
            # Проверяем каждую колонку
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
        """Очищает поле поиска"""
        self.search_input.clear()
    
    def add_variable(self, name: str = "", xpath: str = "", var_type: str = "Static", url: str = "", sample: str = ""):
        """Добавляет переменную в таблицу"""
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
                background-color: #3c3c3c;
                color: #cccccc;
                border: none;
                padding: 2px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                color: #cccccc;
                selection-background-color: #0e639c;
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
        
        # Прокручиваем к новой строке
        self.table.scrollToBottom()
    
    def add_empty_variable(self):
        """Добавляет пустую переменную для заполнения"""
        self.add_variable("new_var", "", "Static", "", "")
    
    def remove_selected(self):
        """Удаляет выбранные строки"""
        selected_rows = set()
        for item in self.table.selectedItems():
            selected_rows.add(item.row())
        
        for row in sorted(selected_rows, reverse=True):
            self.table.removeRow(row)
    
    def clear_all(self):
        """Очищает всю таблицу"""
        self.table.setRowCount(0)
    
    def get_all_variables(self):
        """Возвращает все переменные в виде списка словарей"""
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
        """Импортирует данные из режима Select в таблицу с умным именованием"""
        
        # Определяем базовое имя по приоритетам:
        # 1. Если есть text (не пустой) → используем text
        # 2. Если это картинка (tag == IMG) и есть alt → используем alt
        # 3. Иначе → empty
        if text and text.strip():
            base_name = text.strip()[:30]
        elif tag.upper() == "IMG" and alt and alt.strip():
            base_name = alt.strip()[:30]
        else:
            base_name = "empty"
        
        # Очищаем имя от недопустимых символов
        base_name = re.sub(r'[^a-zA-Z0-9_а-яА-ЯёЁ\s-]', '', base_name)
        base_name = base_name.replace(' ', '_')
        
        # Если после очистки имя пустое, используем "empty"
        if not base_name:
            base_name = "empty"
        
        # Проверяем, сколько раз уже встречалось такое имя
        existing_names = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            if name_item:
                existing_names.append(name_item.text())
        
        # Если имя уже существует, добавляем номер
        final_name = base_name
        counter = 1
        while final_name in existing_names:
            counter += 1
            final_name = f"{base_name}_{counter}"
        
        # Добавляем переменную в таблицу
        self.add_variable(
            name=final_name,
            xpath=xpath,
            var_type="Static",
            url=url,
            sample=text[:50] if text else (alt[:50] if alt else "")
        )
        
        return final_name