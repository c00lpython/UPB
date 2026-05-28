from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QComboBox, QWidget, 
    QVBoxLayout, QHBoxLayout, QPushButton, QHeaderView
)
from PyQt6.QtCore import Qt


class VmTable(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Кнопки управления
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Add Variable")
        self.btn_remove = QPushButton("❌ Remove Selected")
        self.btn_clear = QPushButton("🗑 Clear All")
        
        btn_style = """
            QPushButton {
                background-color: #3c3c3c;
                color: #cccccc;
                padding: 5px 10px;
                border: 1px solid #787878;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
                color: #ffffff;
            }
        """
        
        self.btn_add.setStyleSheet(btn_style)
        self.btn_remove.setStyleSheet(btn_style)
        self.btn_clear.setStyleSheet(btn_style)
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()
        
        # Таблица переменных
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "XPath/CSS", "Type", "URL", "Sample Text"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #252526;
                color: #cccccc;
                gridline-color: #3c3c3c;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #0e639c;
            }
        """)
        
        layout.addLayout(btn_layout)
        layout.addWidget(self.table)
        self.setLayout(layout)
        
        # Подключаем сигналы
        self.btn_add.clicked.connect(self.add_empty_variable)
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_clear.clicked.connect(self.clear_all)
        
        # Добавляем тестовые данные
        self.add_variable("title", "//h1", "Static", "https://example.com", "Example Title")
        self.add_variable("price", "//span[@class='price']", "Dynamic", "https://example.com", "$99.99")
        self.add_variable("description", "//meta[@name='description']/@content", "Static", "https://example.com", "Sample description")
    
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
                border: 1px solid #787878;
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