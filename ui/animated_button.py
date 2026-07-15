# ui/animated_button.py
from PySide6.QtWidgets import QPushButton
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, Qt, Property
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QRadialGradient


class AnimatedButton(QPushButton):
    """Кнопка с плавным hover-эффектом (градиентная обводка)"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        
        self._hover_progress = 0.0
        
        # Анимация для плавного появления обводки
        self.hover_anim = QPropertyAnimation(self, b"hover_progress")
        self.hover_anim.setDuration(250)
        self.hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.setMouseTracking(True)
        self._disable_animation = False
        
        self._colors = {
            "primary": QColor(155, 89, 182),
            "success": QColor(0, 230, 118),
            "danger": QColor(255, 23, 68),
            "default": QColor(255, 255, 255)
        }
    
    @Property(float)
    def hover_progress(self):
        return self._hover_progress
    
    @hover_progress.setter
    def hover_progress(self, value):
        if abs(self._hover_progress - value) > 0.001:
            self._hover_progress = value
            self.update()
    
    def set_animation_enabled(self, enabled: bool):
        self._disable_animation = not enabled
    
    def enterEvent(self, event):
        if not self._disable_animation:
            self.hover_anim.stop()
            self.hover_anim.setStartValue(self._hover_progress)
            self.hover_anim.setEndValue(1.0)
            self.hover_anim.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        if not self._disable_animation:
            self.hover_anim.stop()
            self.hover_anim.setStartValue(self._hover_progress)
            self.hover_anim.setEndValue(0.0)
            self.hover_anim.start()
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # 1. Рисуем стандартную кнопку (из QSS)
        super().paintEvent(event)
        
        # 2. Рисуем градиентную обводку
        if self._hover_progress > 0.01 and not self._disable_animation:
            painter.save()
            
            btn_type = self.property("type") or "default"
            color = self._colors.get(btn_type, self._colors["default"])
            
            # Плавное появление
            alpha = int(80 * self._hover_progress)
            color.setAlpha(alpha)
            
            # Обводка
            pen = QPen(color, 2)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            
            # Закругление 12px
            painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 12, 12)
            
            painter.restore()
        
        painter.end()


class GradientFollowButton(AnimatedButton):
    """Кнопка с эффектом свечения, следующего за мышью"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._mouse_pos = (0.5, 0.5)
        self._glow_radius = 80
        
        # ВАЖНО: Не отключаем анимацию, она нужна для hover_progress
        self._disable_animation = False  # ← ИСПРАВЛЕНО
        self._show_glow = False
    
    def mouseMoveEvent(self, event):
        rect = self.rect()
        pos = event.position()
        x = pos.x() / rect.width()
        y = pos.y() / rect.height()
        self._mouse_pos = (max(0, min(1, x)), max(0, min(1, y)))
        self.update()
        super().mouseMoveEvent(event)
    
    def enterEvent(self, event):
        self._show_glow = True
        self.hover_anim.stop()
        self.hover_anim.setStartValue(self._hover_progress)
        self.hover_anim.setEndValue(1.0)
        self.hover_anim.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._show_glow = False
        self.hover_anim.stop()
        self.hover_anim.setStartValue(self._hover_progress)
        self.hover_anim.setEndValue(0.0)
        self.hover_anim.start()
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        x, y = self._mouse_pos
        
        # 1. Рисуем стандартную кнопку
        super().paintEvent(event)
        
        # 2. Рисуем свечение от позиции мыши
        if self._hover_progress > 0.01 and self._show_glow:
            painter.save()
            
            # Радиальное свечение
            center_x = rect.width() * x
            center_y = rect.height() * y
            radius = self._glow_radius * self._hover_progress
            
            gradient = QRadialGradient(
                center_x, center_y, radius,
                center_x, center_y
            )
            
            # Цвет свечения
            btn_type = self.property("type") or "default"
            colors = {
                "primary": QColor(155, 89, 182),
                "success": QColor(0, 230, 118),
                "danger": QColor(255, 23, 68),
                "default": QColor(255, 255, 255)
            }
            color = QColor(colors.get(btn_type, colors["default"]))
            
            alpha = int(60 * self._hover_progress)
            color.setAlpha(alpha)
            
            gradient.setColorAt(0, color)
            gradient.setColorAt(1, QColor(color.red(), color.green(), color.blue(), 0))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 12, 12)
            
            painter.restore()
        
        painter.end()

class TabButton(AnimatedButton):
    """Кнопка для навигационных табов с линией от центра"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        # Отключаем стандартную обводку
        self._disable_animation = True
        
        # Свойство для активного состояния
        self._active = False
        
        # Анимация для линии (отдельная)
        self.line_anim = QPropertyAnimation(self, b"hover_progress")
        self.line_anim.setDuration(200)  # Быстрее для отзывчивости
        self.line_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
    
    @Property(float)
    def hover_progress(self):
        return self._hover_progress
    
    @hover_progress.setter
    def hover_progress(self, value):
        if abs(self._hover_progress - value) > 0.001:
            self._hover_progress = value
            self.update()
    
    def set_active(self, active: bool):
        self._active = active
        # Мгновенное обновление без анимации для активного состояния
        self._hover_progress = 1.0 if active else 0.0
        self.update()
    
    def enterEvent(self, event):
        """Мышь вошла — показываем линию (если не активна)"""
        if not self._active:
            self.line_anim.stop()
            self.line_anim.setStartValue(self._hover_progress)
            self.line_anim.setEndValue(1.0)
            self.line_anim.start()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Мышь вышла — скрываем линию (если не активна)"""
        if not self._active:
            self.line_anim.stop()
            self.line_anim.setStartValue(self._hover_progress)
            self.line_anim.setEndValue(0.0)
            self.line_anim.start()
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # 1. Рисуем стандартную кнопку (из QSS)
        super().paintEvent(event)
        
        # 2. Рисуем линию снизу (активная ИЛИ при наведении)
        progress = 1.0 if self._active else self._hover_progress
        
        if progress > 0.01:
            painter.save()
            
            # Линия от центра к краям
            margin = int(20 * (1 - progress))
            left = margin
            right = rect.width() - margin
            
            # Цвет линии
            color = QColor(155, 89, 182)
            if self._active:
                color = QColor(124, 77, 255)
            
            pen = QPen(color, 2)
            pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            
            y = rect.height() - 4
            painter.drawLine(left, y, right, y)
            
            painter.restore()
        
        painter.end()