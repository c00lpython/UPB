# ui/vm_table.py
from PySide6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QComboBox, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QHeaderView,
    QLineEdit, QMenu, QApplication, QLabel
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
import re


class VmTable(QWidget):
    view_in_browser_requested = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.setObjectName("VmTable")

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        self.title_label = QLabel("Variables")
        self.title_label.setProperty("vm_title", True)

        self.stats_label = QLabel("0 variables")
        self.stats_label.setProperty("vm_stats", True)
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.stats_label)

        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setProperty("vm_search", True)
        self.search_input.setPlaceholderText("Search variables...")
        self.search_input.textChanged.connect(self.filter_table)

        self.search_column = QComboBox()
        self.search_column.setProperty("vm_filter", True)
        self.search_column.addItems(["All", "Name", "XPath/CSS", "Type", "URL", "Sample Text"])
        self.search_column.setCurrentText("All")

        self.btn_clear_search = QPushButton("✕")
        self.btn_clear_search.setProperty("vm_icon_btn", True)
        self.btn_clear_search.clicked.connect(self.clear_search)

        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.search_column)
        search_layout.addWidget(self.btn_clear_search)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_add = QPushButton("Add Variable")
        self.btn_add.setProperty("primary", True)
        self.btn_remove = QPushButton("Remove Selected")
        self.btn_remove.setProperty("vm_action", True)
        self.btn_clear = QPushButton("Clear All")
        self.btn_clear.setProperty("danger", True)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_clear)
        btn_layout.addStretch()

        self.empty_label = QLabel(
            "No variables yet.\n"
            "Click Add Variable or select elements in the browser."
        )
        self.empty_label.setProperty("vm_empty", True)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setWordWrap(True)

        self.table = QTableWidget()
        self.table.setProperty("vm_table", True)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Name", "XPath/CSS", "Type", "URL", "Sample Text"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setDefaultSectionSize(44)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setStretchLastSection(True)
        self.table.setColumnWidth(2, 110)

        self._name_font = QFont("Segoe UI", 12)
        self._name_font.setWeight(QFont.Weight.DemiBold)
        self._mono_font = QFont("Consolas", 11)
        self._sample_font = QFont("Segoe UI", 11)
        self._sample_font.setItalic(True)

        layout.addLayout(header_layout)
        layout.addLayout(search_layout)
        layout.addLayout(btn_layout)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.btn_add.clicked.connect(self.add_empty_variable)
        self.btn_remove.clicked.connect(self.remove_selected)
        self.btn_clear.clicked.connect(self.clear_all)

        self._update_meta()

    def _apply_widget_style(self, widget):
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _create_type_combo(self, var_type: str) -> QComboBox:
        combo = QComboBox()
        combo.addItems(["Static", "Dynamic", "Network"])
        combo.setCurrentText(var_type)
        combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        combo.setMinimumWidth(100)
        combo.view().setMinimumWidth(130)
        self._style_type_combo(combo, var_type)
        return combo

    def _style_type_combo(self, combo: QComboBox, var_type: str):
        combo.setProperty("vm_type", True)
        combo.setProperty("type_value", var_type)
        combo.currentTextChanged.connect(
            lambda text, c=combo: self._update_type_combo_style(c, text)
        )
        self._update_type_combo_style(combo, var_type)

    def _update_type_combo_style(self, combo: QComboBox, var_type: str):
        combo.setProperty("type_value", var_type)
        self._apply_widget_style(combo)

    def _update_meta(self):
        total = self.table.rowCount()
        visible = sum(
            1 for i in range(total) if not self.table.isRowHidden(i)
        )
        search = self.search_input.text().strip()

        if total == 0:
            self.stats_label.setText("0 variables")
        elif search:
            self.stats_label.setText(f"{visible} of {total} shown")
        else:
            word = "variable" if total == 1 else "variables"
            self.stats_label.setText(f"{total} {word}")

        if total == 0:
            self.empty_label.setText(
                "No variables yet.\n"
                "Click Add Variable or select elements in the browser."
            )
            self.empty_label.show()
            self.table.hide()
        elif visible == 0:
            self.empty_label.setText(f'No matches for "{search}"')
            self.empty_label.show()
            self.table.hide()
        else:
            self.empty_label.hide()
            self.table.show()

    def _show_context_menu(self, pos):
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
        menu.setProperty("vm_context", True)
        self._apply_widget_style(menu)

        header = menu.addAction(f"📦 {var_name}")
        header.setEnabled(False)

        type_action = menu.addAction(f"Type: {var_type}")
        type_action.setEnabled(False)

        menu.addSeparator()

        if url:
            view_action = menu.addAction("View in Browser")
            view_action.setToolTip(f"Open {url} and highlight element by XPath")
            view_action.triggered.connect(
                lambda checked=False, u=url, x=xpath: self.view_in_browser_requested.emit(u, x)
            )
        else:
            no_url = menu.addAction("View in Browser (no URL)")
            no_url.setEnabled(False)

        menu.addSeparator()

        copy_menu = menu.addMenu("Copy")
        copy_menu.setProperty("vm_context", True)
        self._apply_widget_style(copy_menu)

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

        delete_action = menu.addAction("Delete Variable")
        delete_action.triggered.connect(lambda: self._delete_row(row))

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _delete_row(self, row: int):
        if 0 <= row < self.table.rowCount():
            self.table.removeRow(row)
            self._update_meta()

    def filter_table(self):
        search_text = self.search_input.text().lower()

        if not search_text:
            for i in range(self.table.rowCount()):
                self.table.setRowHidden(i, False)
            self._update_meta()
            return

        search_column = self.search_column.currentText()

        for row in range(self.table.rowCount()):
            show_row = False

            if search_column in ("All", "Name"):
                name_item = self.table.item(row, 0)
                if name_item and search_text in name_item.text().lower():
                    show_row = True

            if not show_row and search_column in ("All", "XPath/CSS"):
                xpath_item = self.table.item(row, 1)
                if xpath_item and search_text in xpath_item.text().lower():
                    show_row = True

            if not show_row and search_column in ("All", "Type"):
                combo = self.table.cellWidget(row, 2)
                if combo and search_text in combo.currentText().lower():
                    show_row = True

            if not show_row and search_column in ("All", "URL"):
                url_item = self.table.item(row, 3)
                if url_item and search_text in url_item.text().lower():
                    show_row = True

            if not show_row and search_column in ("All", "Sample Text"):
                sample_item = self.table.item(row, 4)
                if sample_item and search_text in sample_item.text().lower():
                    show_row = True

            self.table.setRowHidden(row, not show_row)

        self._update_meta()

    def clear_search(self):
        self.search_input.clear()

    def add_variable(self, name: str = "", xpath: str = "", var_type: str = "Static", url: str = "", sample: str = ""):
        row = self.table.rowCount()
        self.table.insertRow(row)

        name_item = QTableWidgetItem(name)
        name_item.setFont(self._name_font)
        name_item.setFlags(name_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 0, name_item)

        xpath_item = QTableWidgetItem(xpath)
        xpath_item.setFont(self._mono_font)
        xpath_item.setForeground(QColor("#a0a0b8"))
        xpath_item.setFlags(xpath_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 1, xpath_item)

        combo = QComboBox()
        combo.addItems(["Static", "Dynamic", "Network"])
        combo.setCurrentText(var_type)
        self._style_type_combo(combo, var_type)
        self.table.setCellWidget(row, 2, combo)

        url_item = QTableWidgetItem(url)
        url_item.setFont(self._mono_font)
        url_item.setForeground(QColor("#a0a0b8"))
        url_item.setFlags(url_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 3, url_item)

        sample_item = QTableWidgetItem(sample)
        sample_item.setFont(self._sample_font)
        sample_item.setForeground(QColor("#6a6a82"))
        sample_item.setFlags(sample_item.flags() | Qt.ItemFlag.ItemIsEditable)
        self.table.setItem(row, 4, sample_item)

        self.table.scrollToBottom()
        self._update_meta()

    def add_empty_variable(self):
        self.add_variable("new_var", "", "Static", "", "")

    def remove_selected(self):
        selected_rows = {item.row() for item in self.table.selectedItems()}

        for row in sorted(selected_rows, reverse=True):
            self.table.removeRow(row)

        self._update_meta()

    def clear_all(self):
        self.table.setRowCount(0)
        self._update_meta()

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
