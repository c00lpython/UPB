from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QComboBox, QWidget, 
    QVBoxLayout, QHBoxLayout, QPushButton, QHeaderView,
    QLineEdit
)
from PyQt6.QtCore import Qt


class VmTable(QWidget):
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
                color: ##2d2d2d;
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
                color: ##2d2d2d;
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
        
        # ❌ ОТКЛЮЧАЕМ чередование цветов (зебру)
        self.table.setAlternatingRowColors(False)
        
        # Единый стиль для всей таблицы (без обводок, без белых строк)
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
        """)
        
        # Убираем сетку (белые обводки между ячейками)
        self.table.setShowGrid(False)
        
        layout.addLayout(search_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)
        
        # Подключаем сигналы
        self.btn_add.clicked.connect(self.add_empty_variable)
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_clear.clicked.connect(self.clear_all)
    
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
    
    def import_from_select(self, url: str, xpath: str, text: str, tag: str):
        """Импортирует данные из режима Select в таблицу"""
        var_name = f"{tag.lower()}_{self.table.rowCount()}"
        self.add_variable(
            name=var_name,
            xpath=xpath,
            var_type="Static",
            url=url,
            sample=text[:50] if text else ""
        )
        return var_name