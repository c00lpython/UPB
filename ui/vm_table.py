from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QComboBox, QWidget, QVBoxLayout, QHeaderView
from PyQt6.QtCore import Qt


class VmTable(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "XPath/CSS", "Type", "URL", "Sample Text"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #252526;
                color: #cccccc;
                gridline-color: #3c3c3c;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
        
        layout.addWidget(self.table)
        self.setLayout(layout)
        
        # Добавляем тестовую строку
        self.add_variable("title", "//h1", "Static", "https://example.com", "Example Title")
        self.add_variable("price", "//span[@class='price']", "Dynamic", "https://example.com", "$99.99")
    
    def add_variable(self, name: str, xpath: str, var_type: str, url: str, sample: str):
        row = self.table.rowCount()
        self.table.insertRow(row)
        
        self.table.setItem(row, 0, QTableWidgetItem(name))
        self.table.setItem(row, 1, QTableWidgetItem(xpath))
        
        # ComboBox для типа
        combo = QComboBox()
        combo.addItems(["Static", "Dynamic", "Network"])
        combo.setCurrentText(var_type)
        self.table.setCellWidget(row, 2, combo)
        
        self.table.setItem(row, 3, QTableWidgetItem(url))
        self.table.setItem(row, 4, QTableWidgetItem(sample))