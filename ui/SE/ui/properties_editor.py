# ui/SE/ui/properties_editor.py

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


class SearchableComboBox(QComboBox):
    """ComboBox с фильтрацией по вводимому тексту (БЕЗ автоподстановки)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.lineEdit().textEdited.connect(self.on_text_edited)
        self.all_items = []
        self._updating = False  # Флаг для блокировки рекурсии
        self.setStyleSheet("""
            QComboBox {
                background-color: #3a3a3a;
                color: #ddd;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 11px;
            }
            QComboBox:focus {
                border: 1px solid #3d5afe;
            }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                color: #ddd;
                selection-background-color: #3d5afe;
            }
        """)
    
    def set_items(self, items: list):
        """Устанавливает список всех переменных"""
        print(f"📦 [SearchableComboBox] set_items: {len(items)} items")
        self.all_items = items.copy() if items else []
        self._updating = True
        self.clear()
        if items:
            self.addItems(items)
        self._updating = False
    
    def on_text_edited(self, text):
        """Срабатывает при КАЖДОМ изменении текста (ввод/удаление)"""
        if self._updating:
            return
        print(f"✏️ [SearchableComboBox] textEdited: '{text}'")
        self.filter_items(text)
    
    def filter_items(self, text):
        """Фильтрует список по введённому тексту (startswith)"""
        if self._updating:
            return
            
        print(f"🔍 [SearchableComboBox] filter_items: text='{text}'")
        
        if not self.all_items:
            return
        
        # Блокируем сигналы при обновлении списка
        self._updating = True
        
        # Сохраняем текущий текст
        current_text = self.lineEdit().text()
        
        self.clear()
        
        if not text:
            self.addItems(self.all_items)
        else:
            filtered = [item for item in self.all_items if item.lower().startswith(text.lower())]
            if filtered:
                self.addItems(filtered)
        
        # Восстанавливаем текст (на случай, если он сбросился)
        if self.lineEdit().text() != current_text:
            self.lineEdit().setText(current_text)
        
        self._updating = False
    
    def showPopup(self):
        """Показывает выпадающий список"""
        print(f"🔽 [SearchableComboBox] showPopup, items count: {self.count()}")
        if self.count() > 0:
            super().showPopup()
    
    def hidePopup(self):
        """Скрывает выпадающий список"""
        print(f"🔼 [SearchableComboBox] hidePopup")
        super().hidePopup()
    
    def focusInEvent(self, event):
        """При получении фокуса"""
        print(f"🎯 [SearchableComboBox] focusInEvent")
        super().focusInEvent(event)
    
    def focusOutEvent(self, event):
        """При потере фокуса"""
        print(f"💤 [SearchableComboBox] focusOutEvent, text: '{self.lineEdit().text()}'")
        super().focusOutEvent(event)
    
    def keyPressEvent(self, event):
        """Обработка нажатий клавиш"""
        key = event.key()
        key_name = {
            Qt.Key.Key_Backspace: "Backspace",
            Qt.Key.Key_Delete: "Delete",
            Qt.Key.Key_Left: "Left",
            Qt.Key.Key_Right: "Right",
            Qt.Key.Key_Up: "Up",
            Qt.Key.Key_Down: "Down",
            Qt.Key.Key_Return: "Enter",
            Qt.Key.Key_Enter: "Enter",
            Qt.Key.Key_Tab: "Tab",
            Qt.Key.Key_Escape: "Escape",
        }.get(key, f"Key_{key}")
        
        print(f"⌨️ [SearchableComboBox] keyPressEvent: {key_name}")
        
        if self._updating:
            super().keyPressEvent(event)
            return
        
        if key == Qt.Key.Key_Up:
            print(f"   ⬆️ moving up")
        elif key == Qt.Key.Key_Down:
            print(f"   ⬇️ moving down")
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            print(f"   ✅ Enter pressed, current text: '{self.currentText()}'")
        elif key == Qt.Key.Key_Tab:
            print(f"   ⇆ Tab pressed")
        elif key == Qt.Key.Key_Backspace:
            print(f"   ⌫ Backspace")
        
        super().keyPressEvent(event)

class PropertiesEditor(QWidget):
    """Редактор свойств выбранного блока с поддержкой переменных"""
    
    property_changed = pyqtSignal(int, str, object)  # block_id, prop_name, value
    
    def __init__(self, get_variables_callback=None, parent=None):
        super().__init__(parent)
        self.current_block = None
        self.get_variables_callback = get_variables_callback
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Заголовок
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
        
        # Scroll area
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
        
        # Инфо панель внизу
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
    
    def get_variable_names(self) -> list:
        """Возвращает список имён переменных"""
        if self.get_variables_callback:
            variables = self.get_variables_callback()
            if variables:
                return list(variables.keys())
        return []
    
    def get_variable_value(self, var_name: str) -> dict:
        """Возвращает значение переменной по имени"""
        if self.get_variables_callback:
            variables = self.get_variables_callback()
            return variables.get(var_name, {})
        return {}
    
    def set_block(self, block):
        """Устанавливает блок для редактирования"""
        self.current_block = block
        self.refresh()
    
    def refresh(self):
        """Обновляет UI на основе текущего блока"""
        self.clear()
        
        if not self.current_block:
            self.header.setText("📝 PROPERTIES - No Selection")
            self.info_label.setText("Select a block to edit")
            return
        
        self.header.setText(f"📝 PROPERTIES - {self.current_block.name}")
        self.info_label.setText(f"Editing: {self.current_block.name} (ID: {self.current_block.id})")
        
        params = self.current_block.params
        
        # Группировка свойств по категориям
        categories = self.get_categories(self.current_block.node_type)
        
        for category, props in categories.items():
            self.add_category_header(category)
            for key in props:
                if key in params:
                    self.add_property_row(key, params[key])
    
    def get_categories(self, node_type: str) -> dict:
        """Возвращает группировку свойств по категориям"""
        categories = {
            "startofwork": {
                "⚙️ Basic": ["projectName", "headless", "timeout"]
            },
            "openurl": {
                "🌐 Navigation": ["url", "waitStrategy", "timeout"]
            },
            "click": {
                "🖱️ Interaction": ["selector", "selectorType", "clickCount", "waitAfter"]
            },
            "type": {
                "⌨️ Input": ["selector", "selectorType", "text", "clearFirst", "pressEnter", "delay"]
            },
            "parsedata": {
                "📊 Extraction": ["varName", "saveTo", "extractType", "attributeName"]
            },
            "screenshot": {
                "📸 Capture": ["filename", "fullPage", "selector"]
            },
            "convertexcel": {
                "📑 Conversion": ["inputFile", "outputFormat", "outputFile", "sheetName"]
            },
            "forloop": {
                "🔄 Loop": ["iterator", "iterableType", "iterable"]
            },
            "if": {
                "⚡ Condition": ["left", "operator", "right"]
            },
            "end": {
                "⏹️ Close": ["blockType"]
            },
            "reload": {
                "🔄 Page": ["waitAfter", "ignoreCache"]
            },
            "sendtelegram": {
                "📨 Telegram": ["botToken", "chatId", "message", "parseMode"]
            },
            "savedata": {
                "💾 Output": ["dataVar", "format", "outputPath", "overwrite"]
            },
            "endsession": {
                "🏁 Finish": ["saveResults", "closeBrowser", "exportReport"]
            }
        }
        return categories.get(node_type, {"📦 Properties": list(self.current_block.params.keys()) if self.current_block else []})
    
    def add_category_header(self, title: str):
        """Добавляет заголовок категории"""
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
        """Очищает все поля"""
        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def add_property_row(self, key: str, value):
        """Добавляет строку редактирования свойства"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(12)
        
        # Метка
        label = QLabel(self.format_key(key))
        label.setFixedWidth(110)
        label.setStyleSheet("color: #ccc; font-size: 11px; font-weight: 500;")
        label.setWordWrap(True)
        layout.addWidget(label)
        
        # Редактор (может быть с дроплистом переменных)
        editor = self.create_editor(key, value)
        layout.addWidget(editor, 1)
        
        # Иконка типа
        type_icon = self.get_type_icon(value)
        if type_icon:
            icon_label = QLabel(type_icon)
            icon_label.setStyleSheet("color: #666; font-size: 12px;")
            layout.addWidget(icon_label)
        
        self.container_layout.insertWidget(self.container_layout.count() - 1, widget)
    
    def create_editor(self, key: str, value):
        """Создает виджет редактирования в зависимости от типа и ключа"""
        
        # Поля, которые должны иметь дроплист переменных
        variable_fields = ["url", "selector", "varName", "iterable", "left", "right", "dataVar"]
        
        # Boolean
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
        
        # Number (int/float)
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
        
        # Поля с дроплистом переменных (поиск по началу строки)
        if key in variable_fields:
            editor = SearchableComboBox()
            variable_names = self.get_variable_names()
            if variable_names:
                editor.set_items(variable_names)
            # Устанавливаем текущее значение
            current_text = str(value) if value else ""
            editor.setCurrentText(current_text)
            editor.currentTextChanged.connect(lambda v, k=key: self.on_change(k, v))
            editor.lineEdit().setPlaceholderText("Type value or select variable...")
            return editor
        
        # Dropdown поля (фиксированные опции)
        if key in ["waitStrategy", "selectorType", "iterableType", "operator", "blockType", "parseMode", "outputFormat", "format", "extractType"]:
            editor = self.create_dropdown(key, value)
            return editor
        
        # Обычное текстовое поле
        editor = QLineEdit(str(value))
        editor.textChanged.connect(lambda v, k=key: self.on_change(k, v))
        self.style_editor(editor)
        return editor
    
    def create_dropdown(self, key: str, current_value) -> QComboBox:
        """Создает выпадающий список с фиксированными опциями"""
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
        """Применяет единый стиль к редактору"""
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
        """Возвращает иконку типа значения"""
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
        """Обработчик изменения значения"""
        if self.current_block:
            self.current_block.params[key] = value
            self.property_changed.emit(self.current_block.id, key, value)
    
    def format_key(self, key: str) -> str:
        """Форматирует имя свойства для отображения"""
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