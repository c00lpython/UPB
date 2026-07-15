# ui/SE/ui/properties_editor.py

from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *


class IntelliSensePopup(QWidget):
    """Всплывающее окно IntelliSense"""
    
    item_selected = Signal(str)
    
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
        self.header.setStyleSheet("""
            color: #999; 
            font-size: 9px; 
            padding: 4px 12px 2px 12px; 
            background: transparent; 
            border-bottom: 1px solid #333;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        """)
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
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 12px;
                outline: none;
                padding: 4px 0px;
            }
            QListWidget::item {
                padding: 6px 12px;
                border-left: 3px solid transparent;
                font-family: 'Inter', 'Segoe UI', sans-serif;
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
                background: white;
                width: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(155, 89, 182, 0.8),
                    stop:1 rgba(124, 77, 255, 0.8));
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(155, 89, 182, 1.0),
                    stop:1 rgba(124, 77, 255, 1.0));
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
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
        self.setStyleSheet("""
            QLineEdit {
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 11px;
                background-color: #2a2a2a;
                color: #ccc;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px 8px;
            }
            QLineEdit:focus {
                border: 1px solid #3d5afe;
            }
        """)
    
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
                    return True
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
                background-color: #2a2a2a;
                color: #ccc;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 6px 8px;
                font-size: 11px;
                min-width: 180px;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
            QComboBox:focus { 
                border: 1px solid #3d5afe; 
            }
            QComboBox QAbstractItemView {
                background-color: #2a2a2a;
                color: #ccc;
                selection-background-color: #3d5afe;
                min-width: 300px;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
            QComboBox QAbstractItemView::item {
                font-family: 'Inter', 'Segoe UI', sans-serif;
                padding: 6px 10px;
            }
            QComboBox QAbstractItemView QScrollBar:vertical {
                background: white;
                width: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QComboBox QAbstractItemView QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(155, 89, 182, 0.8),
                    stop:1 rgba(124, 77, 255, 0.8));
                border-radius: 4px;
                min-height: 20px;
            }
            QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(155, 89, 182, 1.0),
                    stop:1 rgba(124, 77, 255, 1.0));
            }
            QComboBox QAbstractItemView QScrollBar::add-line:vertical,
            QComboBox QAbstractItemView QScrollBar::sub-line:vertical {
                height: 0px;
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
                    return True
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


# ============================================================================
# PROPERTIES EDITOR С ГЛОБАЛЬНЫМ ТРЕКЕРОМ
# ============================================================================

class PropertiesEditor(QWidget):
    """Редактор свойств блоков с глобальным трекером мыши"""
    
    property_changed = Signal(int, str, object)
    
    def __init__(self, get_variables_callback=None, parent=None):
        super().__init__(parent)
        
        self._mouse_pos = (0.5, 0.5)
        self._hover_progress = 0.0
        self._show_glow = False
        self._is_hovering = False
        self._target_progress = 0.0
        self._tracker_connected = False
        
        # Анимация для плавного появления свечения
        self.hover_anim = QPropertyAnimation(self, b"hover_progress")
        self.hover_anim.setDuration(150)
        self.hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.current_block = None
        self.get_variables_callback = get_variables_callback
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setObjectName("PropertiesEditor")
        
        # Подключаемся к глобальному трекеру
        self._setup_global_tracker()
        
        self.setup_ui()
    
    def _setup_global_tracker(self):
        """Подключается к глобальному трекеру мыши"""
        if self._tracker_connected:
            return
            
        try:
            from ui.main_window import mouse_tracker
            mouse_tracker.mouse_moved.connect(self._on_global_mouse_move)
            mouse_tracker.widget_hovered.connect(self._on_global_widget_hover)
            self._tracker_connected = True
            print("✅ PropertiesEditor connected to mouse tracker")
        except ImportError:
            QTimer.singleShot(100, self._setup_global_tracker)
        except Exception as e:
            print(f"⚠️ Failed to connect to mouse tracker: {e}")
    
    def _on_global_mouse_move(self, x, y):
        """Обработчик движения мыши от глобального трекера"""
        if not self._is_hovering:
            return
        
        if self.is_deleted():
            return
            
        widget_pos = self.mapFromGlobal(QPoint(x, y))
        rect = self.rect()
        
        if rect.contains(widget_pos):
            if rect.width() > 0 and rect.height() > 0:
                norm_x = widget_pos.x() / rect.width()
                norm_y = widget_pos.y() / rect.height()
                self._mouse_pos = (max(0, min(1, norm_x)), max(0, min(1, norm_y)))
                self.update()
    
    def _on_global_widget_hover(self, widget):
        """Обработчик смены виджета под курсором"""
        if self.is_deleted():
            return
        
        is_over = False
        try:
            is_over = widget == self or (widget and self.isAncestorOf(widget)) if widget else False
        except RuntimeError:
            return
        
        if is_over and not self._is_hovering:
            self._is_hovering = True
            self._show_glow = True
            self._target_progress = 1.0
            self.hover_anim.stop()
            self.hover_anim.setStartValue(self._hover_progress)
            self.hover_anim.setEndValue(1.0)
            self.hover_anim.start()
            
        elif not is_over and self._is_hovering:
            self._is_hovering = False
            self._show_glow = False
            self._target_progress = 0.0
            self.hover_anim.stop()
            self.hover_anim.setStartValue(self._hover_progress)
            self.hover_anim.setEndValue(0.0)
            self.hover_anim.start()
    
    def is_deleted(self):
        try:
            _ = self.windowTitle()
            return False
        except RuntimeError:
            return True
    
    @Property(float)
    def hover_progress(self):
        return self._hover_progress
    
    @hover_progress.setter
    def hover_progress(self, value):
        if abs(self._hover_progress - value) > 0.001:
            self._hover_progress = value
            self.update()
    
    def paint_glow_effect(self, painter):
        """Рисует эффект свечения только для фона виджета"""
        if self._is_hovering and self._hover_progress > 0.01:
            painter.save()
            
            rect = self.rect()
            x, y = self._mouse_pos
            
            center_x = rect.width() * x
            center_y = rect.height() * y
            radius = max(rect.width(), rect.height()) * 0.5 * self._hover_progress
            
            gradient = QRadialGradient(
                center_x, center_y, radius,
                center_x, center_y
            )
            
            color = QColor(155, 89, 182)
            alpha = int(40 * self._hover_progress)
            color.setAlpha(alpha)
            
            gradient.setColorAt(0, color)
            gradient.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 4, 4)
            
            pen_color = QColor(155, 89, 182)
            pen_alpha = int(60 * self._hover_progress)
            pen_color.setAlpha(pen_alpha)
            painter.setPen(QPen(pen_color, 1.5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(rect.adjusted(1, 1, -2, -2), 4, 4)
            
            painter.restore()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.header = QLabel("📝 PROPERTIES")
        self.header.setFixedHeight(40)
        self.header.setStyleSheet("""
            QLabel {
                background-color: #0a0a0a;
                color: #3d5afe;
                font-weight: bold;
                font-size: 12px;
                padding-left: 15px;
                border-bottom: 1px solid #1a1a1a;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
        """)
        layout.addWidget(self.header)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea { 
                border: none; 
                background: transparent; 
            }
            QScrollBar:vertical {
                background: white;
                width: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(155, 89, 182, 0.6),
                    stop:1 rgba(124, 77, 255, 0.6));
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(155, 89, 182, 0.8),
                    stop:1 rgba(124, 77, 255, 0.8));
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background: white;
                height: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(155, 89, 182, 0.6),
                    stop:1 rgba(124, 77, 255, 0.6));
                border-radius: 4px;
                min-width: 30px;
            }
            QScrollBar::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(155, 89, 182, 0.8),
                    stop:1 rgba(124, 77, 255, 0.8));
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)
        
        self.container = QWidget()
        self.container.setStyleSheet("""
            QWidget {
                background: transparent;
            }
        """)
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(15, 15, 15, 15)
        self.container_layout.setSpacing(12)
        self.container_layout.addStretch()
        
        scroll.setWidget(self.container)
        layout.addWidget(scroll)
        
        info_panel = QWidget()
        info_panel.setFixedHeight(50)
        info_panel.setStyleSheet("background: #0a0a0a; border-top: 1px solid #1a1a1a;")
        info_layout = QHBoxLayout(info_panel)
        info_layout.setContentsMargins(15, 5, 15, 5)
        
        self.info_label = QLabel("Select a block to edit")
        self.info_label.setStyleSheet("""
            color: #555; 
            font-size: 11px;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        """)
        info_layout.addWidget(self.info_label)
        info_layout.addStretch()
        
        layout.addWidget(info_panel)


    def paintEvent(self, event):
        """Отрисовка с эффектом свечения только для фона"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # 1. Черный фон
        painter.fillRect(rect, QColor(10, 10, 10))
        
        # 2. Рамка
        painter.setPen(QPen(QColor(30, 30, 30), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect.adjusted(0, 0, -1, -1), 4, 4)
        
        # 3. Эффект свечения ТОЛЬКО для фона
        self.paint_glow_effect(painter)
        
        painter.end()
        
        # Рисуем дочерние виджеты поверх (без изменений)
        for child in self.children():
            if isinstance(child, QWidget) and child.isVisible() and child != self:
                child_painter = QPainter(self)
                child_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                child.render(child_painter, child.pos())
                child_painter.end()
    
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
                font-family: 'Inter', 'Segoe UI', sans-serif;
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
        label.setStyleSheet("""
            color: #aaa; 
            font-size: 11px; 
            font-weight: 600;
            font-family: 'Inter', 'Segoe UI', sans-serif;
        """)
        label.setWordWrap(True)
        layout.addWidget(label)
        
        editor = self.create_editor(key, value)
        layout.addWidget(editor, 1)
        
        type_icon = self.get_type_icon(value)
        if type_icon:
            icon_label = QLabel(type_icon)
            icon_label.setStyleSheet("color: #555; font-size: 12px; font-family: 'Inter', 'Segoe UI', sans-serif;")
            layout.addWidget(icon_label)
        
        self.container_layout.insertWidget(self.container_layout.count() - 1, widget)
    
    def create_editor(self, key: str, value):
        variable_fields = ["url", "selector", "varName", "iterable", "left", "right", "dataVar"]
        
        if isinstance(value, bool):
            editor = QCheckBox()
            editor.setChecked(value)
            editor.stateChanged.connect(lambda state, k=key: self.on_change(k, state == Qt.CheckState.Checked))
            editor.setStyleSheet("""
                QCheckBox {
                    font-family: 'Inter', 'Segoe UI', sans-serif;
                    color: #aaa;
                }
                QCheckBox::indicator {
                    width: 18px;
                    height: 18px;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #1a1a1a;
                    border: 1px solid #333;
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    background-color: #3d5afe;
                    border: 1px solid #3d5afe;
                    border-radius: 3px;
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
        editor.setStyleSheet("""
            QComboBox {
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 11px;
                background-color: #1a1a1a;
                color: #aaa;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 6px 8px;
            }
            QComboBox:focus {
                border: 1px solid #3d5afe;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a;
                color: #aaa;
                selection-background-color: #3d5afe;
                font-family: 'Inter', 'Segoe UI', sans-serif;
            }
            QComboBox QAbstractItemView::item {
                font-family: 'Inter', 'Segoe UI', sans-serif;
                padding: 6px 10px;
            }
            QComboBox QAbstractItemView QScrollBar:vertical {
                background: white;
                width: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QComboBox QAbstractItemView QScrollBar::handle:vertical {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(155, 89, 182, 0.6),
                    stop:1 rgba(124, 77, 255, 0.6));
                border-radius: 4px;
                min-height: 20px;
            }
            QComboBox QAbstractItemView QScrollBar::handle:vertical:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(155, 89, 182, 0.8),
                    stop:1 rgba(124, 77, 255, 0.8));
            }
            QComboBox QAbstractItemView QScrollBar::add-line:vertical,
            QComboBox QAbstractItemView QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        return editor
    
    def style_editor(self, widget):
        widget.setStyleSheet("""
            QLineEdit, QSpinBox, QDoubleSpinBox {
                font-family: 'Inter', 'Segoe UI', sans-serif;
                font-size: 11px;
                background-color: #1a1a1a;
                color: #aaa;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 6px 8px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
                border: 1px solid #3d5afe;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #333;
                width: 20px;
                border: none;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                background-color: #333;
                width: 20px;
                border: none;
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