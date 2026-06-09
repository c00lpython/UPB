from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


class SearchableComboBox(QComboBox):
    """ComboBox с поиском/фильтрацией"""
    
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
                padding: 4px 6px;
                font-size: 11px;
            }
            QComboBox:focus { border: 1px solid #3d5afe; }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                color: #ddd;
                selection-background-color: #3d5afe;
            }
        """)
    
    def set_items(self, items: list, variables_data: dict = None):
        self._updating = True
        self.clear()
        self.variables_data = variables_data or {}
        
        if items and isinstance(items[0], tuple):
            self.all_items = items.copy()
            for idx, (display, actual) in enumerate(items):
                self.addItem(display)
                if actual in self.variables_data:
                    data = self.variables_data[actual]
                    tooltip = f"📦 {actual}"
                    if data.get('selector'):
                        tooltip += f"\n🎯 {data['selector'][:50]}"
                    if data.get('sample'):
                        tooltip += f"\n📝 {data['sample'][:50]}"
                    self.setItemData(idx, tooltip, Qt.ItemDataRole.ToolTipRole)
        else:
            self.all_items = [(item, item) for item in items]
            for display, actual in self.all_items:
                self.addItem(display)
        
        self.filtered_items = self.all_items.copy()
        self._updating = False
    
    def get_actual_value(self) -> str:
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
                tooltip = f"📦 {actual}"
                if data.get('selector'):
                    tooltip += f"\n🎯 {data['selector'][:50]}"
                self.setItemData(idx, tooltip, Qt.ItemDataRole.ToolTipRole)
        
        if self.lineEdit().text() != current_text:
            self.lineEdit().setText(current_text)
        
        self._updating = False
    
    def showPopup(self):
        if self.count() > 0:
            super().showPopup()


class CodeEditorWithCompleter(QTextEdit):
    """Текстовый редактор с QCompleter (как в VSCode)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 6px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
            QTextEdit:focus {
                border: 1px solid #3d5afe;
            }
        """)
        
        self.completer = None
    
    def set_completer(self, completer: QCompleter):
        """Устанавливает QCompleter для автокомплита"""
        # Отключаем старый completer
        if self.completer:
            try:
                self.completer.activated.disconnect()
            except:
                pass
        
        self.completer = completer
        
        if not completer:
            return
        
        completer.setWidget(self)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        
        # Подключаем сигнал
        completer.activated.connect(self._insert_completion)
        
        # Настраиваем всплывающее окно
        popup = completer.popup()
        popup.setStyleSheet("""
            QListView {
                background-color: #252526;
                color: #d4d4d4;
                border: 1px solid #3d5afe;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                outline: none;
            }
            QListView::item {
                padding: 4px 8px;
            }
            QListView::item:selected {
                background-color: #3d5afe;
                color: white;
            }
        """)
    
    def _get_text_under_cursor(self) -> str:
        """Возвращает слово под курсором (для автокомплита)"""
        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        return cursor.selectedText()
    
    def keyPressEvent(self, event):
        # Если комплитер активен и показан - обрабатываем навигацию
        if self.completer and self.completer.popup().isVisible():
            if event.key() == Qt.Key.Key_Tab:
                # TAB - вставляем выбранный вариант
                self._insert_current_completion()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Down:
                # Стрелка вниз - следующий элемент
                current = self.completer.popup().currentIndex()
                next_row = current.row() + 1
                if next_row < self.completer.completionModel().rowCount():
                    self.completer.popup().setCurrentIndex(
                        self.completer.completionModel().index(next_row, 0)
                    )
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Up:
                # Стрелка вверх - предыдущий элемент
                current = self.completer.popup().currentIndex()
                prev_row = current.row() - 1
                if prev_row >= 0:
                    self.completer.popup().setCurrentIndex(
                        self.completer.completionModel().index(prev_row, 0)
                    )
                event.accept()
                return
            elif event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
                # Enter - вставляем и подтверждаем
                self._insert_current_completion()
                event.accept()
                return
            elif event.key() == Qt.Key.Key_Escape:
                self.completer.popup().hide()
                event.accept()
                return
        
        # Обычная обработка
        super().keyPressEvent(event)
        
        # Автоматический показ комплитера при вводе
        if self.completer and not self.completer.popup().isVisible():
            # Не показываем при навигационных клавишах
            if event.key() in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt,
                               Qt.Key.Key_Meta, Qt.Key.Key_Tab, Qt.Key.Key_Backtab):
                return
            
            # Получаем текущее слово
            completion_prefix = self._get_text_under_cursor()
            
            # Показываем комплитер если слово начинается с 'v'
            if len(completion_prefix) >= 1 and completion_prefix[0].lower() == 'v':
                self.completer.setCompletionPrefix(completion_prefix)
                
                # Показываем комплитер
                cursor_rect = self.cursorRect()
                cursor_rect.setWidth(self.completer.popup().sizeHintForColumn(0) + 20)
                self.completer.complete(cursor_rect)
                
                # Выбираем первый элемент если есть
                if self.completer.popup().isVisible() and self.completer.completionModel().rowCount() > 0:
                    self.completer.popup().setCurrentIndex(
                        self.completer.completionModel().index(0, 0)
                    )
            else:
                self.completer.popup().hide()
    
    def _insert_current_completion(self):
        """Вставляет текущий выбранный вариант из комплитера"""
        if self.completer and self.completer.popup().isVisible():
            current_index = self.completer.popup().currentIndex()
            if current_index.isValid():
                completion = self.completer.completionModel().data(current_index, Qt.ItemDataRole.DisplayRole)
                if completion:
                    self._insert_completion(completion)
    
    def _insert_completion(self, completion: str):
        """Вставляет выбранное завершение в текст"""
        if self.completer and self.completer.widget() != self:
            return
        
        cursor = self.textCursor()
        
        # Удаляем текущее слово под курсором
        cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        cursor.removeSelectedText()
        
        # Вставляем завершение
        cursor.insertText(completion)
        self.setTextCursor(cursor)
        
        # Скрываем комплитер
        if self.completer:
            self.completer.popup().hide()

class ConditionVariableWidget(QWidget):
    """Виджет для valN - компактная версия"""
    
    value_changed = pyqtSignal(str, str)
    delete_requested = pyqtSignal(str)
    
    def __init__(self, var_name: str, value: str = "", get_variables_callback=None, parent=None):
        super().__init__(parent)
        self.var_name = var_name
        self.get_variables_callback = get_variables_callback
        self.setup_ui(value)
    
    def setup_ui(self, current_value):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)
        
        name_label = QLabel(self.var_name)
        name_label.setFixedWidth(35)
        name_label.setStyleSheet("""
            QLabel {
                color: #3d5afe;
                font-weight: bold;
                font-size: 10px;
                background: #2d2d2d;
                border-radius: 3px;
                padding: 3px;
            }
        """)
        layout.addWidget(name_label)
        
        self.value_combo = SearchableComboBox()
        self.value_combo.setMinimumWidth(160)
        
        if self.get_variables_callback:
            variables = self.get_variables_callback()
            items = [("✏️ custom", "custom")]
            for var_name in variables.keys():
                items.append((var_name, var_name))
            self.value_combo.set_items(items, variables)
        
        if current_value:
            found = False
            for i in range(self.value_combo.count()):
                if self.value_combo.itemText(i) == current_value:
                    self.value_combo.setCurrentIndex(i)
                    found = True
                    break
            if not found:
                self.value_combo.setCurrentText(current_value)
        
        self.value_combo.currentTextChanged.connect(self._on_value_changed)
        layout.addWidget(self.value_combo, 1)
        
        delete_btn = QPushButton("✕")
        delete_btn.setFixedSize(20, 20)
        delete_btn.setStyleSheet("""
            QPushButton {
                background: #e74c3c;
                color: white;
                border: none;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover { background: #c0392b; }
        """)
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.var_name))
        layout.addWidget(delete_btn)
    
    def _on_value_changed(self, text):
        actual = self.value_combo.get_actual_value()
        if actual == "custom":
            actual = text
        self.value_changed.emit(self.var_name, actual)
    
    def get_value(self) -> str:
        actual = self.value_combo.get_actual_value()
        if actual == "custom":
            return self.value_combo.currentText()
        return actual


class IfBlockProperties(QWidget):
    """IfBlock свойства с автокомплитом как в VSCode"""
    
    property_changed = pyqtSignal(dict)
    
    def __init__(self, block, get_variables_callback=None, parent=None):
        super().__init__(parent)
        self.block = block
        self.get_variables_callback = get_variables_callback
        self.val_widgets = {}
        self._completer_model = None
        self.setup_ui()
        self.load_from_block()
    
    def _update_completer_model(self):
        """Обновляет модель комплитера текущими valN переменными"""
        word_list = list(self.val_widgets.keys())
        # Добавляем Python ключевые слова
        keywords = ["and", "or", "not", "True", "False", "None", "in", "is"]
        word_list.extend(keywords)
        word_list = sorted(set(word_list))  # Уникальные и сортированные
        
        self._completer_model = QStringListModel(word_list)
        completer = QCompleter(self._completer_model)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        
        self.code_editor.set_completer(completer)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Переменные
        vars_group = QGroupBox("📦 Variables")
        vars_group.setStyleSheet("""
            QGroupBox {
                color: #3d5afe;
                font-weight: bold;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 8px;
                font-size: 11px;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 5px; }
        """)
        vars_layout = QVBoxLayout(vars_group)
        vars_layout.setSpacing(4)
        
        self.vars_container = QWidget()
        self.vars_layout_inner = QVBoxLayout(self.vars_container)
        self.vars_layout_inner.setContentsMargins(2, 2, 2, 2)
        self.vars_layout_inner.setSpacing(4)
        self.vars_layout_inner.addStretch()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.vars_container)
        scroll.setMaximumHeight(200)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        vars_layout.addWidget(scroll)
        
        add_btn = QPushButton("+ Add valN")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #3d5afe;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px;
                font-size: 10px;
            }
            QPushButton:hover { background: #5c7cfa; }
        """)
        add_btn.clicked.connect(self._add_variable)
        vars_layout.addWidget(add_btn)
        
        layout.addWidget(vars_group)
        
        # Условие
        cond_group = QGroupBox("⚡ Condition")
        cond_group.setStyleSheet(vars_group.styleSheet())
        cond_layout = QVBoxLayout(cond_group)
        
        hint = QLabel("💡 Python expression: val1 == val2 and val3 > 10")
        hint.setStyleSheet("color: #888; font-size: 9px;")
        cond_layout.addWidget(hint)
        
        hint2 = QLabel("   Type 'v' for variables list | TAB to insert")
        hint2.setStyleSheet("color: #3d5afe; font-size: 9px;")
        cond_layout.addWidget(hint2)
        
        self.code_editor = CodeEditorWithCompleter()
        self.code_editor.setMaximumHeight(100)
        self.code_editor.setPlaceholderText("val1 == 'active' and val2 > 100")
        self.code_editor.textChanged.connect(self._on_condition_changed)
        cond_layout.addWidget(self.code_editor)
        
        validate_btn = QPushButton("✓ Validate")
        validate_btn.setStyleSheet("""
            QPushButton {
                background: #27ae60;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 4px;
                font-size: 10px;
            }
            QPushButton:hover { background: #2ecc71; }
        """)
        validate_btn.clicked.connect(self._validate)
        cond_layout.addWidget(validate_btn)
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-size: 9px;")
        cond_layout.addWidget(self.status_label)
        
        layout.addWidget(cond_group)
        layout.addStretch()
    
    def _add_variable(self):
        nums = []
        for name in self.val_widgets.keys():
            if name.startswith('val'):
                try:
                    nums.append(int(name[3:]))
                except:
                    pass
        next_num = max(nums) + 1 if nums else 1
        var_name = f"val{next_num}"
        
        widget = ConditionVariableWidget(var_name, "", self.get_variables_callback, self)
        widget.value_changed.connect(self._on_value_changed)
        widget.delete_requested.connect(self._remove_variable)
        
        self.val_widgets[var_name] = widget
        self.vars_layout_inner.insertWidget(self.vars_layout_inner.count() - 1, widget)
        self._update_completer_model()
        self._emit_changed()
    
    def _remove_variable(self, var_name: str):
        if var_name in self.val_widgets:
            self.val_widgets[var_name].deleteLater()
            del self.val_widgets[var_name]
            
            # Удаляем из условия
            condition = self.code_editor.toPlainText()
            import re
            condition = re.sub(rf'\b{var_name}\b', '', condition)
            condition = re.sub(r'\s+', ' ', condition).strip()
            self.code_editor.setPlainText(condition)
            
            self._update_completer_model()
            self._emit_changed()
    
    def _on_value_changed(self, var_name: str, value: str):
        self._emit_changed()
    
    def _on_condition_changed(self):
        self._emit_changed()
    
    def _validate(self):
        condition = self.code_editor.toPlainText().strip()
        if not condition:
            self.status_label.setText("⚠️ Empty")
            self.status_label.setStyleSheet("color: #f39c12; font-size: 9px;")
            return
        
        import re
        val_vars = re.findall(r'val\d+', condition)
        
        try:
            compile(condition, '<string>', 'eval')
            if val_vars:
                self.status_label.setText(f"✅ Valid | Used: {', '.join(set(val_vars))}")
            else:
                self.status_label.setText("✅ Valid syntax")
            self.status_label.setStyleSheet("color: #2ecc71; font-size: 9px;")
        except SyntaxError as e:
            self.status_label.setText(f"❌ {str(e).splitlines()[0]}")
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 9px;")
    
    def _emit_changed(self):
        data = {'variables': {}, 'condition': self.code_editor.toPlainText().strip()}
        for name, widget in self.val_widgets.items():
            data['variables'][name] = widget.get_value()
        
        self.block.params['condition_data'] = data
        self.block.params['condition'] = data['condition']
        for name, value in data['variables'].items():
            self.block.params[name] = value
        
        self.property_changed.emit(data)
    
    def load_from_block(self):
        condition_data = self.block.params.get('condition_data', {})
        variables = condition_data.get('variables', {})
        
        if not variables:
            for key, value in self.block.params.items():
                if key.startswith('val') and key[3:].isdigit():
                    variables[key] = value
        
        for var_name, value in variables.items():
            widget = ConditionVariableWidget(var_name, value, self.get_variables_callback, self)
            widget.value_changed.connect(self._on_value_changed)
            widget.delete_requested.connect(self._remove_variable)
            self.val_widgets[var_name] = widget
            self.vars_layout_inner.insertWidget(self.vars_layout_inner.count() - 1, widget)
        
        if not self.val_widgets:
            self._add_variable()
        
        condition = self.block.params.get('condition', '')
        if condition_data.get('condition'):
            condition = condition_data.get('condition', '')
        self.code_editor.setPlainText(condition)
        
        self._update_completer_model()


class PropertiesEditor(QWidget):
    
    property_changed = pyqtSignal(int, str, object)
    
    def __init__(self, get_variables_callback=None, parent=None):
        super().__init__(parent)
        self.current_block = None
        self.get_variables_callback = get_variables_callback
        self.if_block_widget = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.header = QLabel("📝 PROPERTIES")
        self.header.setFixedHeight(35)
        self.header.setStyleSheet("""
            QLabel {
                background: #2d2d2d;
                color: #3d5afe;
                font-weight: bold;
                font-size: 11px;
                padding-left: 12px;
                border-bottom: 1px solid #444;
            }
        """)
        layout.addWidget(self.header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: #252525; }
            QScrollBar:vertical { background: #252525; width: 8px; }
            QScrollBar::handle:vertical { background: #444; border-radius: 4px; }
        """)
        
        self.container = QWidget()
        self.container.setStyleSheet("background: #252525;")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(10, 10, 10, 10)
        self.container_layout.setSpacing(10)
        self.container_layout.addStretch()
        
        scroll.setWidget(self.container)
        layout.addWidget(scroll)
        
        info_panel = QWidget()
        info_panel.setFixedHeight(40)
        info_panel.setStyleSheet("background: #2d2d2d; border-top: 1px solid #444;")
        info_layout = QHBoxLayout(info_panel)
        info_layout.setContentsMargins(12, 5, 12, 5)
        
        self.info_label = QLabel("Select a block to edit")
        self.info_label.setStyleSheet("color: #666; font-size: 10px;")
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()
        
        layout.addWidget(info_panel)
    
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
        self.info_label.setText(f"Editing: {self.current_block.name}")
        
        if self.current_block.node_type == "if":
            self.if_block_widget = IfBlockProperties(
                self.current_block, 
                self.get_variables_callback,
                self
            )
            self.if_block_widget.property_changed.connect(
                lambda d: self.property_changed.emit(self.current_block.id, "condition_data", d)
            )
            self.container_layout.insertWidget(self.container_layout.count() - 1, self.if_block_widget)
        else:
            params = self.current_block.params
            categories = self._get_categories(self.current_block.node_type)
            
            for category, props in categories.items():
                self._add_category_header(category)
                for key in props:
                    if key in params:
                        self._add_property_row(key, params[key])
    
    def _get_categories(self, node_type: str) -> dict:
        categories = {
            "startofwork": {"⚙️": ["projectName", "headless", "timeout"]},
            "openurl": {"🌐": ["url", "waitStrategy", "timeout"]},
            "click": {"🖱️": ["selector", "selectorType", "clickCount", "waitAfter"]},
            "type": {"⌨️": ["selector", "selectorType", "text", "clearFirst", "pressEnter"]},
            "parsedata": {"📊": ["varName", "saveTo", "extractType", "attributeName"]},
            "screenshot": {"📸": ["filename", "fullPage", "selector"]},
            "forloop": {"🔄": ["iterator", "iterableType", "iterable"]},
            "if": {"⚡": []},
        }
        return categories.get(node_type, {"📦": list(self.current_block.params.keys()) if self.current_block else []})
    
    def _add_category_header(self, title: str):
        label = QLabel(title)
        label.setStyleSheet("""
            QLabel {
                color: #3d5afe;
                font-weight: bold;
                font-size: 10px;
                padding: 6px 0 2px 0;
                border-bottom: 1px solid #3d5afe40;
            }
        """)
        self.container_layout.insertWidget(self.container_layout.count() - 1, label)
    
    def _add_property_row(self, key: str, value):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 3, 0, 3)
        layout.setSpacing(8)
        
        label = QLabel(self._format_key(key))
        label.setFixedWidth(100)
        label.setStyleSheet("color: #ccc; font-size: 10px;")
        layout.addWidget(label)
        
        editor = self._create_editor(key, value)
        layout.addWidget(editor, 1)
        
        self.container_layout.insertWidget(self.container_layout.count() - 1, widget)
    
    def _create_editor(self, key: str, value):
        if isinstance(value, bool):
            cb = QCheckBox()
            cb.setChecked(value)
            cb.stateChanged.connect(lambda s, k=key: self._on_change(k, s == Qt.CheckState.Checked))
            return cb
        
        if isinstance(value, int):
            spin = QSpinBox()
            spin.setRange(-999999, 999999)
            spin.setValue(value)
            spin.valueChanged.connect(lambda v, k=key: self._on_change(k, v))
            self._style_editor(spin)
            return spin
        
        if key in ["url", "selector", "varName", "iterable"]:
            combo = SearchableComboBox()
            vars_data = self.get_variables_callback() if self.get_variables_callback else {}
            filter_type = "url" if "url" in key.lower() else "selector"
            filtered = self._get_filtered_vars(filter_type)
            if filtered:
                combo.set_items(filtered, vars_data)
            combo.setCurrentText(str(value))
            combo.currentTextChanged.connect(lambda v, k=key: self._on_change(k, combo.get_actual_value()))
            self._style_editor(combo)
            return combo
        
        if key in ["waitStrategy", "selectorType", "iterableType", "operator"]:
            options = {
                "waitStrategy": ["load", "domcontentloaded", "networkidle"],
                "selectorType": ["css", "xpath"],
                "iterableType": ["list", "range", "variable"],
                "operator": ["eq", "ne", "gt", "lt", "contains", "startswith", "endswith"]
            }
            combo = QComboBox()
            combo.addItems(options.get(key, []))
            combo.setCurrentText(str(value))
            combo.currentTextChanged.connect(lambda v, k=key: self._on_change(k, v))
            self._style_editor(combo)
            return combo
        
        editor = QLineEdit(str(value))
        editor.textChanged.connect(lambda v, k=key: self._on_change(k, v))
        self._style_editor(editor)
        return editor
    
    def _style_editor(self, widget):
        widget.setStyleSheet("""
            QLineEdit, QSpinBox, QComboBox {
                background: #3a3a3a;
                color: #ddd;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 4px 6px;
                font-size: 10px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 1px solid #3d5afe;
            }
        """)
    
    def _on_change(self, key: str, value):
        if self.current_block:
            self.current_block.params[key] = value
            self.property_changed.emit(self.current_block.id, key, value)
    
    def _format_key(self, key: str) -> str:
        names = {
            "projectName": "Project", "headless": "Headless", "timeout": "Timeout",
            "url": "URL", "waitStrategy": "Wait", "selector": "Selector",
            "selectorType": "Type", "clickCount": "Clicks", "waitAfter": "Wait (ms)",
            "text": "Text", "clearFirst": "Clear", "pressEnter": "Enter",
            "varName": "Var name", "saveTo": "Save to", "extractType": "Extract",
            "attributeName": "Attribute", "filename": "File", "fullPage": "Full page",
            "iterator": "Iterator", "iterableType": "Type", "iterable": "Iterable"
        }
        return names.get(key, key.replace("_", " ").title())
    
    def _get_filtered_vars(self, filter_type: str) -> list:
        if not self.get_variables_callback:
            return []
        vars_data = self.get_variables_callback()
        if filter_type == "url":
            seen = set()
            result = []
            for name, data in vars_data.items():
                url = data.get('url', '').strip()
                if url and url not in seen:
                    seen.add(url)
                    display = url[:50] + "..." if len(url) > 50 else url
                    result.append((display, name))
            return result
        else:
            return [(name, name) for name, data in vars_data.items() if data.get('selector', '').strip()]
    
    def clear(self):
        if self.if_block_widget:
            self.if_block_widget.deleteLater()
            self.if_block_widget = None
        while self.container_layout.count() > 1:
            item = self.container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()