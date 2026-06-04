# ui/SE/ui/properties_editor.py

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


class SearchableComboBox(QComboBox):
    """ComboBox с поиском/фильтрацией - показывает только имена переменных, тултип с данными"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.lineEdit().textEdited.connect(self.on_text_edited)
        self.all_items = []
        self.filtered_items = []
        self.variables_data = {}
        self._updating = False
        self.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a;
                color: #ddd;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 11px;
                min-width: 180px;
            }
            QComboBox:focus {
                border: 1px solid #3d5afe;
            }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                color: #ddd;
                selection-background-color: #3d5afe;
                min-width: 300px;
            }
        """)
    
    def set_items(self, items: list, variables_data: dict = None):
        """
        items: список кортежей (display_text, actual_value)
        variables_data: словарь с данными переменных для тултипов
        """
        self._updating = True
        self.clear()
        self.variables_data = variables_data or {}
        
        if items and isinstance(items[0], tuple):
            self.all_items = items.copy()
            for idx, (display, actual) in enumerate(items):
                self.addItem(display)
                if actual in self.variables_data:
                    data = self.variables_data[actual]
                    selector = data.get('selector', '')
                    url = data.get('url', '')
                    sample = data.get('sample', '')
                    tooltip = f"📦 Variable: {actual}\n"
                    if selector:
                        tooltip += f"🎯 XPath: {selector[:80]}{'...' if len(selector) > 80 else ''}\n"
                    if url:
                        tooltip += f"🌐 URL: {url}\n"
                    if sample:
                        tooltip += f"📝 Sample: {sample[:60]}{'...' if len(sample) > 60 else ''}"
                    self.setItemData(idx, tooltip, Qt.ItemDataRole.ToolTipRole)
        else:
            self.all_items = [(item, item) for item in items]
            for display, actual in self.all_items:
                self.addItem(display)
        
        self.filtered_items = self.all_items.copy()
        self._updating = False
        print(f"📦 [Combo] set_items: {len(self.all_items)} items")
    
    def get_actual_value(self) -> str:
        """Возвращает actual value текущего выбранного элемента"""
        current_text = self.currentText()
        for display, actual in self.all_items:
            if display == current_text:
                return actual
        return current_text
    
    def on_text_edited(self, text):
        if self._updating:
            return
        self._filter_items(text)
    
    def _filter_items(self, text):
        if self._updating or not self.all_items:
            return
        
        self._updating = True
        current_text = self.lineEdit().text()
        
        self.clear()
        
        if not text:
            self.filtered_items = self.all_items.copy()
        else:
            self.filtered_items = [(d, a) for d, a in self.all_items if d.lower().startswith(text.lower())]
        
        for idx, (display, actual) in enumerate(self.filtered_items):
            self.addItem(display)
            if actual in self.variables_data:
                data = self.variables_data[actual]
                selector = data.get('selector', '')
                url = data.get('url', '')
                sample = data.get('sample', '')
                tooltip = f"📦 Variable: {actual}\n"
                if selector:
                    tooltip += f"🎯 XPath: {selector[:80]}{'...' if len(selector) > 80 else ''}\n"
                if url:
                    tooltip += f"🌐 URL: {url}\n"
                if sample:
                    tooltip += f"📝 Sample: {sample[:60]}{'...' if len(sample) > 60 else ''}"
                self.setItemData(idx, tooltip, Qt.ItemDataRole.ToolTipRole)
        
        if self.lineEdit().text() != current_text:
            self.lineEdit().setText(current_text)
        
        self._updating = False
    
    def showPopup(self):
        if self.count() > 0:
            super().showPopup()
    
    def focusOutEvent(self, event):
        super().focusOutEvent(event)


class PropertiesEditor(QWidget):
    
    property_changed = pyqtSignal(int, str, object)
    
    def __init__(self, get_variables_callback=None, parent=None):
        super().__init__(parent)
        self.current_block = None
        self.get_variables_callback = get_variables_callback
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.header = QLabel("📝 PROPERTIES")
        self.header.setFixedHeight(40)
        self.header.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                color: #3d5afe;
                font-weight: bold;
                font-size: 12px;
                padding-left: 15px;
                border-bottom: 1px solid #444;
            }
        """)
        layout.addWidget(self.header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #252525;
            }
            QScrollBar:vertical {
                background: #252525;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #444;
                border-radius: 5px;
            }
        """)
        
        self.container = QWidget()
        self.container.setStyleSheet("background: #252525;")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(15, 15, 15, 15)
        self.container_layout.setSpacing(12)
        self.container_layout.addStretch()
        
        scroll.setWidget(self.container)
        layout.addWidget(scroll)
        
        info_panel = QWidget()
        info_panel.setFixedHeight(50)
        info_panel.setStyleSheet("background: #2d2d2d; border-top: 1px solid #444;")
        info_layout = QHBoxLayout(info_panel)
        info_layout.setContentsMargins(15, 5, 15, 5)
        
        self.info_label = QLabel("Select a block to edit")
        self.info_label.setStyleSheet("color: #666; font-size: 11px;")
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()
        
        layout.addWidget(info_panel)
    
    def _get_filter_type_by_key(self, key: str) -> str:
        """
        Определяет тип фильтрации по имени поля (регистронезависимо)
        """
        key_lower = key.lower()
        
        if "url" in key_lower:
            return "url"
        
        if any(x in key_lower for x in ["selector", "xpath", "css", "var"]):
            return "selector"
        
        return "all"
    
    def _get_placeholder_by_key(self, key: str) -> str:
        """Возвращает placeholder в зависимости от поля"""
        key_lower = key.lower()
        
        if "url" in key_lower:
            return "Type URL or select unique URL variable..."
        if any(x in key_lower for x in ["selector", "xpath", "css", "var"]):
            return "Type XPath/CSS or select variable..."
        return "Type value or select variable..."
    
    def get_unique_urls(self) -> list:
        """
        Возвращает список уникальных URL из переменных
        Возвращает список кортежей (display_text, actual_value)
        display_text = сокращённый URL (первые 60 символов)
        actual_value = имя переменной (для сохранения в params)
        """
        print(f"🔍 [UNIQUE_URLS] START")
        
        if not self.get_variables_callback:
            return []
        
        variables = self.get_variables_callback()
        if not variables:
            return []
        
        filtered = []
        seen_urls = set()
        
        for name, data in variables.items():
            url_val = data.get('url', '').strip()
            
            if url_val and url_val not in seen_urls:
                seen_urls.add(url_val)
                
                # Обрезаем URL для отображения (первые 60 символов)
                if len(url_val) > 60:
                    display_url = url_val[:57] + "..."
                else:
                    display_url = url_val
                
                filtered.append((display_url, name))
                print(f"   ✅ {display_url} → {name}")
            elif url_val:
                print(f"   ⚠️ {name} (duplicate URL) - SKIPPED")
            else:
                print(f"   ❌ {name} (no URL)")
        
        print(f"🎯 [UNIQUE_URLS] result: {len(filtered)} unique URLs")
        return filtered

    def get_filtered_variables(self, filter_type: str) -> list:
        """
        Возвращает список кортежей (display_text, actual_value) для дроплиста
        filter_type: 'selector', 'all'
        """
        print(f"🔍 [FILTER] filter_type={filter_type}")
        
        if not self.get_variables_callback:
            return []
        
        variables = self.get_variables_callback()
        if not variables:
            return []
        
        filtered = []
        
        for name, data in variables.items():
            selector_val = data.get('selector', '').strip()
            
            if filter_type == "selector":
                if selector_val:
                    filtered.append((name, name))
                    print(f"   ✅ {name} (has selector)")
                else:
                    print(f"   ❌ {name} (no selector)")
            else:  # all
                filtered.append((name, name))
                print(f"   ✅ {name} (all mode)")
        
        print(f"🎯 [FILTER] result: {len(filtered)} items")
        return filtered
    
    def set_block(self, block):
        self.current_block = block
        self.refresh()
    
    def refresh(self):
        self.clear()
        
        if not self.current_block:
            self.header.setText("📝 PROPERTIES - No Selection")
            self.info_label.setText("Select a block to edit")
            return
        
        self.header.setText(f"📝 PROPERTIES - {self.current_block.name}")
        self.info_label.setText(f"Editing: {self.current_block.name} (ID: {self.current_block.id})")
        
        params = self.current_block.params
        categories = self.get_categories(self.current_block.node_type)
        
        for category, props in categories.items():
            self.add_category_header(category)
            for key in props:
                if key in params:
                    self.add_property_row(key, params[key])
    
    def get_categories(self, node_type: str) -> dict:
        categories = {
            "startofwork": {"⚙️ Basic": ["projectName", "headless", "timeout"]},
            "openurl": {"🌐 Navigation": ["url", "waitStrategy", "timeout"]},
            "click": {"🖱️ Interaction": ["selector", "selectorType", "clickCount", "waitAfter", "waitForNavigation"]},
            "type": {"⌨️ Input": ["selector", "selectorType", "text", "clearFirst", "pressEnter", "delay"]},
            "parsedata": {"📊 Extraction": ["varName", "saveTo", "extractType", "attributeName"]},
            "screenshot": {"📸 Capture": ["filename", "fullPage", "selector"]},
            "convertexcel": {"📑 Conversion": ["inputFile", "outputFormat", "outputFile", "sheetName"]},
            "forloop": {"🔄 Loop": ["iterator", "iterableType", "iterable"]},
            "if": {"⚡ Condition": ["left", "operator", "right"]},
            "end": {"⏹️ Close": ["blockType"]},
            "reload": {"🔄 Page": ["waitAfter", "ignoreCache"]},
            "sendtelegram": {"📨 Telegram": ["botToken", "chatId", "message", "parseMode"]},
            "savedata": {"💾 Output": ["dataVar", "format", "outputPath", "overwrite"]},
            "endsession": {"🏁 Finish": ["saveResults", "closeBrowser", "exportReport"]}
        }
        return categories.get(node_type, {"📦 Properties": list(self.current_block.params.keys()) if self.current_block else []})
    
    def add_category_header(self, title: str):
        label = QLabel(title)
        label.setStyleSheet("""
            QLabel {
                color: #3d5afe;
                font-weight: bold;
                font-size: 11px;
                letter-spacing: 1px;
                padding: 8px 0 4px 0;
                border-bottom: 1px solid #3d5afe40;
            }
        """)
        self.container_layout.insertWidget(self.container_layout.count() - 1, label)
    
    def clear(self):
        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def add_property_row(self, key: str, value):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)
        
        label = QLabel(self.format_key(key))
        label.setFixedWidth(110)
        label.setStyleSheet("color: #ccc; font-size: 11px; font-weight: 500;")
        label.setWordWrap(True)
        layout.addWidget(label)
        
        editor = self.create_editor(key, value)
        layout.addWidget(editor, 1)
        
        type_icon = self.get_type_icon(value)
        if type_icon:
            icon_label = QLabel(type_icon)
            icon_label.setStyleSheet("color: #666; font-size: 12px;")
            layout.addWidget(icon_label)
        
        self.container_layout.insertWidget(self.container_layout.count() - 1, widget)
    
    def create_editor(self, key: str, value):
        variable_fields = ["url", "selector", "varName", "iterable", "left", "right", "dataVar"]
        
        if isinstance(value, bool):
            editor = QCheckBox()
            editor.setChecked(value)
            editor.stateChanged.connect(lambda state, k=key: self.on_change(k, state == Qt.CheckState.Checked))
            editor.setStyleSheet("""
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                    border-radius: 4px;
                    background-color: #3a3a3a;
                    border: 1px solid #555;
                }
                QCheckBox::indicator:checked {
                    background-color: #3d5afe;
                    border-color: #3d5afe;
                }
            """)
            return editor
        
        if isinstance(value, int):
            editor = QSpinBox()
            editor.setRange(-999999, 999999)
            editor.setValue(value)
            editor.valueChanged.connect(lambda v, k=key: self.on_change(k, v))
            self.style_editor(editor)
            return editor
        
        if isinstance(value, float):
            editor = QDoubleSpinBox()
            editor.setRange(-999999, 999999)
            editor.setDecimals(2)
            editor.setValue(value)
            editor.valueChanged.connect(lambda v, k=key: self.on_change(k, v))
            self.style_editor(editor)
            return editor
        
        if key in variable_fields and self.current_block:
            editor = SearchableComboBox()
            filter_type = self._get_filter_type_by_key(key)
            variables_data = self.get_variables_callback() if self.get_variables_callback else {}
            
            # Для URL полей используем get_unique_urls
            if filter_type == "url":
                filtered_vars = self.get_unique_urls()
                print(f"🔍 [EDITOR] key={key}, using UNIQUE_URLS, got {len(filtered_vars)} items")
            else:
                filtered_vars = self.get_filtered_variables(filter_type)
                print(f"🔍 [EDITOR] key={key}, filter_type={filter_type}, got {len(filtered_vars)} items")
            
            if filtered_vars:
                editor.set_items(filtered_vars, variables_data)
            else:
                print(f"⚠️ [EDITOR] No variables for key={key}")
            
            current_value = str(value) if value else ""
            for display, actual in filtered_vars:
                if actual == current_value:
                    editor.setCurrentText(display)
                    break
            else:
                editor.setCurrentText(current_value)
            
            editor.currentTextChanged.connect(lambda v, k=key: self.on_combo_change(k, v, editor))
            editor.lineEdit().setPlaceholderText(self._get_placeholder_by_key(key))
            return editor
        
        if key in ["waitStrategy", "selectorType", "iterableType", "operator", "blockType", "parseMode", "outputFormat", "format", "extractType"]:
            editor = self.create_dropdown(key, value)
            return editor
        
        editor = QLineEdit(str(value))
        editor.textChanged.connect(lambda v, k=key: self.on_change(k, v))
        self.style_editor(editor)
        return editor
    
    def on_combo_change(self, key: str, display_text: str, combo: SearchableComboBox):
        """Обработчик изменения комбобокса - извлекаем actual value"""
        actual_value = combo.get_actual_value()
        self.on_change(key, actual_value)
    
    def create_dropdown(self, key: str, current_value) -> QComboBox:
        options = {
            "waitStrategy": ["domcontentloaded", "load", "networkidle"],
            "selectorType": ["css", "xpath"],
            "iterableType": ["list", "range", "variable"],
            "operator": ["contains", "endswith", "eq", "gt", "lt", "ne", "startswith"],
            "blockType": ["if", "loop"],
            "parseMode": ["", "HTML", "MarkdownV2"],
            "outputFormat": ["csv", "excel", "json", "sqlite"],
            "format": ["csv", "excel", "json", "sqlite"],
            "extractType": ["attribute", "html", "text"]
        }
        
        editor = QComboBox()
        items = options.get(key, [])
        editor.addItems(items)
        current = str(current_value) if current_value else items[0] if items else ""
        editor.setCurrentText(current)
        editor.currentTextChanged.connect(lambda v, k=key: self.on_change(k, v))
        self.style_editor(editor)
        return editor
    
    def style_editor(self, widget):
        widget.setStyleSheet("""
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: #3a3a3a;
                color: #ddd;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 11px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border: 1px solid #3d5afe;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #555;
                width: 20px;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #aaa;
                margin-right: 8px;
            }
        """)
    
    def get_type_icon(self, value) -> str:
        if isinstance(value, bool):
            return "✓/✗"
        if isinstance(value, int):
            return "123"
        if isinstance(value, float):
            return "1.0"
        if isinstance(value, str):
            if value.startswith("{{") and value.endswith("}}"):
                return "🔗"
            if "://" in value:
                return "🌐"
            return "📝"
        return ""
    
    def on_change(self, key: str, value):
        if self.current_block:
            self.current_block.params[key] = value
            self.property_changed.emit(self.current_block.id, key, value)
    
    def format_key(self, key: str) -> str:
        names = {
            "projectName": "Project Name",
            "headless": "Headless Mode",
            "timeout": "Timeout (s)",
            "url": "URL",
            "waitStrategy": "Wait Strategy",
            "selector": "Selector",
            "selectorType": "Selector Type",
            "clickCount": "Click Count",
            "waitAfter": "Wait After (ms)",
            "waitForNavigation": "Wait for Navigation",
            "text": "Text",
            "clearFirst": "Clear First",
            "pressEnter": "Press Enter",
            "delay": "Delay (ms)",
            "varName": "Variable Name",
            "saveTo": "Save To",
            "extractType": "Extract Type",
            "attributeName": "Attribute Name",
            "filename": "Filename",
            "fullPage": "Full Page",
            "inputFile": "Input File",
            "outputFormat": "Output Format",
            "outputFile": "Output File",
            "sheetName": "Sheet Name",
            "iterator": "Iterator",
            "iterableType": "Iterable Type",
            "iterable": "Iterable",
            "left": "Left Operand",
            "operator": "Operator",
            "right": "Right Operand",
            "blockType": "Block Type",
            "ignoreCache": "Ignore Cache",
            "botToken": "Bot Token",
            "chatId": "Chat ID",
            "message": "Message",
            "parseMode": "Parse Mode",
            "dataVar": "Data Variable",
            "format": "Output Format",
            "outputPath": "Output Path",
            "overwrite": "Overwrite",
            "saveResults": "Save Results",
            "closeBrowser": "Close Browser",
            "exportReport": "Export Report"
        }
        return names.get(key, key.replace("_", " ").title())