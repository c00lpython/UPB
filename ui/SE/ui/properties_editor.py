from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


class IntelliSensePopup(QWidget):
    """Всплывающее окно IntelliSense"""
    
    item_selected = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(2, 2, 2, 2)
        
        content_widget = QWidget()
        content_widget.setObjectName("intelliContent")
        content_widget.setStyleSheet("""
            #intelliContent {
                background-color: #252526;
                border: 1px solid #3d5afe;
                border-radius: 6px;
            }
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 3)
        content_widget.setGraphicsEffect(shadow)
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        self.header = QLabel()
        self.header.setFixedHeight(24)
        self.header.setStyleSheet("color: #999; font-size: 9px; padding: 4px 12px 2px 12px; background: transparent; border-bottom: 1px solid #333;")
        self.header.hide()
        content_layout.addWidget(self.header)
        
        self.list_widget = QListWidget()
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                color: #d4d4d4;
                border: none;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                outline: none;
                padding: 4px 0px;
            }
            QListWidget::item {
                padding: 6px 12px;
                border-left: 3px solid transparent;
            }
            QListWidget::item:selected {
                background-color: #094771;
                color: #ffffff;
                border-left: 3px solid #0078d4;
            }
            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
            QScrollBar:vertical {
                background: #1e1e1e;
                width: 6px;
            }
            QScrollBar::handle:vertical {
                background: #424242;
                border-radius: 3px;
                min-height: 20px;
            }
        """)
        content_layout.addWidget(self.list_widget)
        
        main_layout.addWidget(content_widget)
        
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        
        self.setFixedWidth(280)
        self.max_items_visible = 8
    
    def _on_item_clicked(self, item):
        if item:
            text = item.text()
            self.hide()
            self.item_selected.emit(text)
    
    def set_items(self, items: list, title: str = "", filter_text: str = ""):
        self.list_widget.clear()
        
        if not items:
            self.hide()
            return
        
        if title:
            self.header.setText(title)
            self.header.show()
        else:
            self.header.hide()
        
        if filter_text:
            starts = [i for i in items if i.lower().startswith(filter_text.lower())]
            others = [i for i in items if i not in starts]
            sorted_items = starts + others
        else:
            sorted_items = items
        
        for text in sorted_items:
            item = QListWidgetItem(text)
            item.setSizeHint(QSize(0, 28))
            self.list_widget.addItem(item)
        
        header_h = 24 if title else 0
        visible = min(len(sorted_items), self.max_items_visible)
        visible = max(visible, 1)
        h = header_h + (visible * 28) + 4
        self.setFixedHeight(h)
        
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
    
    def select_next(self):
        cur = self.list_widget.currentRow()
        if cur < self.list_widget.count() - 1:
            self.list_widget.setCurrentRow(cur + 1)
    
    def select_prev(self):
        cur = self.list_widget.currentRow()
        if cur > 0:
            self.list_widget.setCurrentRow(cur - 1)
    
    def get_current_item(self) -> str:
        item = self.list_widget.currentItem()
        return item.text() if item else None
    
    def underMouse(self) -> bool:
        return self.rect().contains(self.mapFromGlobal(QCursor.pos()))


class CompleterLineEdit(QLineEdit):
    """QLineEdit с IntelliSense popup"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._popup = None
        self._completion_words = []
        self._variables_data = {}
    
    def set_completion_words(self, words: list, variables_data: dict = None):
        self._completion_words = sorted(set(words))
        self._variables_data = variables_data or {}
    
    def _get_word_under_cursor(self) -> tuple:
        cursor_pos = self.cursorPosition()
        text = self.text()
        start = cursor_pos
        while start > 0 and (text[start-1].isalnum() or text[start-1] in ['_', '.', '{', '}']):
            start -= 1
        return start, text[start:cursor_pos]
    
    def _get_context(self) -> tuple:
        _, word = self._get_word_under_cursor()
        word = word.replace('{{', '').replace('{', '').replace('}', '')
        
        if '.' in word:
            parts = word.rsplit('.', 1)
            var_name = parts[0].strip()
            filter_key = parts[1].strip() if len(parts) > 1 else ""
            return (filter_key, "keys", var_name)
        else:
            return (word.strip(), "variables", "")
    
    def _show_popup(self):
        filter_text, context, var_name = self._get_context()
        
        if context == "keys" and var_name in self._variables_data:
            data = self._variables_data[var_name]
            keys = []
            
            keys.append(f"Name: {var_name}")
            if data.get('selector'):
                keys.append(f"XPath: {data['selector'][:60]}")
            if data.get('url'):
                keys.append(f"URL: {data['url'][:60]}")
            if data.get('sample'):
                sample = str(data['sample']).replace('\n', ' ')[:60]
                keys.append(f"Sample: {sample}")
            
            if filter_text:
                keys = [k for k in keys if filter_text.lower() in k.lower()]
            
            if keys:
                if not self._popup:
                    self._popup = IntelliSensePopup(self.window())
                    self._popup.item_selected.connect(self._insert_completion)
                self._popup.set_items(keys, f"📦 {var_name} keys", filter_text)
                pos = self.mapToGlobal(QPoint(0, self.height() + 2))
                self._popup.move(pos)
                self._popup.show()
            else:
                if self._popup:
                    self._popup.hide()
        
        elif context == "variables":
            if filter_text:
                matches = [w for w in self._completion_words if filter_text.lower() in w.lower()]
            else:
                matches = self._completion_words.copy()
            
            if matches:
                if not self._popup:
                    self._popup = IntelliSensePopup(self.window())
                    self._popup.item_selected.connect(self._insert_completion)
                self._popup.set_items(matches, "📝 Variables", filter_text)
                pos = self.mapToGlobal(QPoint(0, self.height() + 2))
                self._popup.move(pos)
                self._popup.show()
            else:
                if self._popup:
                    self._popup.hide()
    
    def _insert_completion(self, completion: str):
        if not completion:
            return
        
        _, context, var_name = self._get_context()
        
        if context == "keys":
            start, word = self._get_word_under_cursor()
            text = self.text()
            
            if ': ' in completion:
                key_name = completion.split(': ')[0].lower()
            else:
                key_name = completion.lower()
            
            dot_pos = text.rfind('.', 0, start + len(word))
            if dot_pos >= 0:
                new_text = text[:dot_pos + 1] + key_name + text[start + len(word):]
                self.setText(new_text)
                self.setCursorPosition(dot_pos + 1 + len(key_name))
            else:
                new_text = text[:start] + key_name + text[start + len(word):]
                self.setText(new_text)
                self.setCursorPosition(start + len(key_name))
        else:
            start, word = self._get_word_under_cursor()
            text = self.text()
            new_text = text[:start] + completion + text[start + len(word):]
            self.setText(new_text)
            self.setCursorPosition(start + len(completion))
        
        self.setFocus()
        self.activateWindow()
    
    def event(self, event):
        """Перехватываем ВСЕ события для блокировки Tab"""
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            
            if self._popup and self._popup.isVisible():
                if key == Qt.Key.Key_Tab:
                    item = self._popup.get_current_item()
                    if item:
                        self._insert_completion(item)
                        self._show_popup()
                    return True  # ПОГЛОЩАЕМ Tab
                elif key == Qt.Key.Key_Down:
                    self._popup.select_next()
                    return True
                elif key == Qt.Key.Key_Up:
                    self._popup.select_prev()
                    return True
                elif key in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
                    item = self._popup.get_current_item()
                    if item:
                        self._insert_completion(item)
                        self._show_popup()
                    return True
                elif key == Qt.Key.Key_Escape:
                    self._popup.hide()
                    return True
            
            result = super().event(event)
            if event.text() and event.text().isprintable():
                self._show_popup()
            elif key == Qt.Key.Key_Backspace:
                self._show_popup()
            elif key == Qt.Key.Key_Delete:
                self._show_popup()
            return result
        
        elif event.type() == QEvent.Type.FocusOut:
            if self._popup and self._popup.isVisible():
                QTimer.singleShot(100, self._check_hide_popup)
            return super().event(event)
        
        return super().event(event)
    
    def _check_hide_popup(self):
        if self._popup and self._popup.isVisible():
            if not self.hasFocus() and not self._popup.underMouse():
                self._popup.hide()


class SearchableComboBox(QComboBox):
    """ComboBox с IntelliSense popup"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        self.line_edit = self.lineEdit()
        self.line_edit.textEdited.connect(self._on_text_edited)
        
        self._popup = None
        self._completion_words = []
        self._variables_data = {}
        self.all_items = []
        self.filtered_items = []
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
            QComboBox:focus { border: 1px solid #3d5afe; }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                color: #ddd;
                selection-background-color: #3d5afe;
                min-width: 300px;
            }
        """)
    
    def set_completion_words(self, words: list, variables_data: dict = None):
        self._completion_words = sorted(set(words))
        self._variables_data = variables_data or {}
    
    def _get_word_under_cursor(self) -> tuple:
        cursor_pos = self.line_edit.cursorPosition()
        text = self.line_edit.text()
        start = cursor_pos
        while start > 0 and (text[start-1].isalnum() or text[start-1] in ['_', '.', '{', '}']):
            start -= 1
        return start, text[start:cursor_pos]
    
    def _get_context(self) -> tuple:
        _, word = self._get_word_under_cursor()
        word = word.replace('{{', '').replace('{', '').replace('}', '')
        
        if '.' in word:
            parts = word.rsplit('.', 1)
            var_name = parts[0].strip()
            filter_key = parts[1].strip() if len(parts) > 1 else ""
            return (filter_key, "keys", var_name)
        else:
            return (word.strip(), "variables", "")
    
    def _show_popup(self):
        filter_text, context, var_name = self._get_context()
        
        if context == "keys" and var_name in self._variables_data:
            data = self._variables_data[var_name]
            keys = []
            
            keys.append(f"Name: {var_name}")
            if data.get('selector'):
                keys.append(f"XPath: {data['selector'][:60]}")
            if data.get('url'):
                keys.append(f"URL: {data['url'][:60]}")
            if data.get('sample'):
                sample = str(data['sample']).replace('\n', ' ')[:60]
                keys.append(f"Sample: {sample}")
            
            if filter_text:
                keys = [k for k in keys if filter_text.lower() in k.lower()]
            
            if keys:
                if not self._popup:
                    self._popup = IntelliSensePopup(self.window())
                    self._popup.item_selected.connect(self._insert_completion)
                self._popup.set_items(keys, f"📦 {var_name} keys", filter_text)
                pos = self.mapToGlobal(QPoint(0, self.height() + 2))
                self._popup.move(pos)
                self._popup.show()
            else:
                if self._popup:
                    self._popup.hide()
        
        elif context == "variables":
            if filter_text:
                matches = [w for w in self._completion_words if filter_text.lower() in w.lower()]
            else:
                matches = self._completion_words.copy()
            
            if matches:
                if not self._popup:
                    self._popup = IntelliSensePopup(self.window())
                    self._popup.item_selected.connect(self._insert_completion)
                self._popup.set_items(matches, "📝 Variables", filter_text)
                pos = self.mapToGlobal(QPoint(0, self.height() + 2))
                self._popup.move(pos)
                self._popup.show()
            else:
                if self._popup:
                    self._popup.hide()
    
    def _insert_completion(self, completion: str):
        if not completion:
            return
        
        _, context, var_name = self._get_context()
        
        if context == "keys":
            start, word = self._get_word_under_cursor()
            text = self.line_edit.text()
            
            if ': ' in completion:
                key_name = completion.split(': ')[0].lower()
            else:
                key_name = completion.lower()
            
            dot_pos = text.rfind('.', 0, start + len(word))
            if dot_pos >= 0:
                new_text = text[:dot_pos + 1] + key_name + text[start + len(word):]
                self.line_edit.setText(new_text)
                self.line_edit.setCursorPosition(dot_pos + 1 + len(key_name))
            else:
                new_text = text[:start] + key_name + text[start + len(word):]
                self.line_edit.setText(new_text)
                self.line_edit.setCursorPosition(start + len(key_name))
        else:
            start, word = self._get_word_under_cursor()
            text = self.line_edit.text()
            new_text = text[:start] + completion + text[start + len(word):]
            self.line_edit.setText(new_text)
            self.line_edit.setCursorPosition(start + len(completion))
        
        self.line_edit.setFocus()
        self.line_edit.activateWindow()
        self._update_combo_value()
    
    def _update_combo_value(self):
        text = self.line_edit.text()
        idx = self.findText(text)
        if idx >= 0:
            self.setCurrentIndex(idx)
    
    def set_items(self, items: list, variables_data: dict = None):
        self._updating = True
        self.clear()
        self._variables_data = variables_data or {}
        self.all_items = [(name, name) for name in items]
        
        for idx, (display, actual) in enumerate(self.all_items):
            self.addItem(display)
        
        self.filtered_items = self.all_items.copy()
        self._updating = False
    
    def get_actual_value(self) -> str:
        current_text = self.currentText()
        for display, actual in self.all_items:
            if display == current_text:
                return actual
        return current_text
    
    def _on_text_edited(self, text):
        if self._updating:
            return
        self._show_popup()
        self._filter_combo_items(text)
    
    def _filter_combo_items(self, text):
        if self._updating or not self.all_items:
            return
        
        self._updating = True
        current_text = self.line_edit.text()
        self.clear()
        
        if not text:
            self.filtered_items = self.all_items.copy()
        else:
            self.filtered_items = [(d, a) for d, a in self.all_items if d.lower().startswith(text.lower())]
        
        for display, actual in self.filtered_items:
            self.addItem(display)
        
        if self.line_edit.text() != current_text:
            self.line_edit.setText(current_text)
        
        self._updating = False
    
    def event(self, event):
        """Перехватываем ВСЕ события для блокировки Tab"""
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            
            if self._popup and self._popup.isVisible():
                if key == Qt.Key.Key_Tab:
                    item = self._popup.get_current_item()
                    if item:
                        self._insert_completion(item)
                        self._show_popup()
                    return True  # ПОГЛОЩАЕМ Tab
                elif key == Qt.Key.Key_Down:
                    self._popup.select_next()
                    return True
                elif key == Qt.Key.Key_Up:
                    self._popup.select_prev()
                    return True
                elif key in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
                    item = self._popup.get_current_item()
                    if item:
                        self._insert_completion(item)
                        self._show_popup()
                    return True
                elif key == Qt.Key.Key_Escape:
                    self._popup.hide()
                    return True
            
            return super().event(event)
        
        elif event.type() == QEvent.Type.FocusOut:
            if self._popup and self._popup.isVisible():
                QTimer.singleShot(100, self._check_hide_popup)
            return super().event(event)
        
        return super().event(event)
    
    def _check_hide_popup(self):
        if self._popup and self._popup.isVisible():
            if not self.line_edit.hasFocus() and not self._popup.underMouse():
                self._popup.hide()
    
    def showPopup(self):
        if self.count() > 0:
            super().showPopup()
            if self._popup:
                self._popup.hide()


class PropertiesEditor(QWidget):
    """Редактор свойств блоков"""
    
    property_changed = pyqtSignal(int, str, object)
    
    def __init__(self, get_variables_callback=None, parent=None):
        super().__init__(parent)
        self.current_block = None
        self.get_variables_callback = get_variables_callback
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
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
            QScrollArea { border: none; background: #252525; }
            QScrollBar:vertical { background: #252525; width: 10px; }
            QScrollBar::handle:vertical { background: #444; border-radius: 5px; }
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
    
    def get_variable_names(self) -> list:
        if self.get_variables_callback:
            variables = self.get_variables_callback()
            return list(variables.keys())
        return []
    
    def get_variables_data(self) -> dict:
        if self.get_variables_callback:
            return self.get_variables_callback()
        return {}
    
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
            variable_names = self.get_variable_names()
            variables_data = self.get_variables_data()
            
            if variable_names:
                editor.set_items(variable_names, variables_data)
                editor.set_completion_words(variable_names, variables_data)
            
            current_value = str(value) if value else ""
            editor.setCurrentText(current_value)
            editor.currentTextChanged.connect(lambda v, k=key: self.on_combo_change(k, v, editor))
            return editor
        
        if key in ["text", "message", "filename", "projectName"]:
            editor = CompleterLineEdit()
            editor.setText(str(value))
            editor.textChanged.connect(lambda v, k=key: self.on_change(k, v))
            variable_names = self.get_variable_names()
            variables_data = self.get_variables_data()
            editor.set_completion_words(variable_names, variables_data)
            self.style_editor(editor)
            return editor
        
        if key in ["waitStrategy", "selectorType", "iterableType", "operator", "blockType", "parseMode", "outputFormat", "format", "extractType"]:
            return self.create_dropdown(key, value)
        
        editor = QLineEdit(str(value))
        editor.textChanged.connect(lambda v, k=key: self.on_change(k, v))
        self.style_editor(editor)
        return editor
    
    def on_combo_change(self, key: str, display_text: str, combo: SearchableComboBox):
        self.on_change(key, combo.get_actual_value())
    
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
            QSpinBox::up-button, QSpinBox::down-button { background-color: #555; width: 20px; }
            QComboBox::drop-down { border: none; width: 24px; }
            QComboBox::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #aaa;
                margin-right: 8px;
            }
        """)
    
    def get_type_icon(self, value) -> str:
        if isinstance(value, bool): return "✓/✗"
        if isinstance(value, int): return "123"
        if isinstance(value, float): return "1.0"
        if isinstance(value, str):
            if value.startswith("{{") and value.endswith("}}"): return "🔗"
            if "://" in value: return "🌐"
            return "📝"
        return ""
    
    def on_change(self, key: str, value):
        if self.current_block:
            self.current_block.params[key] = value
            self.property_changed.emit(self.current_block.id, key, value)
    
    def format_key(self, key: str) -> str:
        names = {
            "projectName": "Project Name", "headless": "Headless Mode", "timeout": "Timeout (s)",
            "url": "URL", "waitStrategy": "Wait Strategy", "selector": "Selector",
            "selectorType": "Selector Type", "clickCount": "Click Count", "waitAfter": "Wait After (ms)",
            "waitForNavigation": "Wait for Navigation", "text": "Text", "clearFirst": "Clear First",
            "pressEnter": "Press Enter", "delay": "Delay (ms)", "varName": "Variable Name",
            "saveTo": "Save To", "extractType": "Extract Type", "attributeName": "Attribute Name",
            "filename": "Filename", "fullPage": "Full Page", "inputFile": "Input File",
            "outputFormat": "Output Format", "outputFile": "Output File", "sheetName": "Sheet Name",
            "iterator": "Iterator", "iterableType": "Iterable Type", "iterable": "Iterable",
            "left": "Left Operand", "operator": "Operator", "right": "Right Operand",
            "blockType": "Block Type", "ignoreCache": "Ignore Cache", "botToken": "Bot Token",
            "chatId": "Chat ID", "message": "Message", "parseMode": "Parse Mode",
            "dataVar": "Data Variable", "format": "Output Format", "outputPath": "Output Path",
            "overwrite": "Overwrite", "saveResults": "Save Results", "closeBrowser": "Close Browser",
            "exportReport": "Export Report"
        }
        return names.get(key, key.replace("_", " ").title())