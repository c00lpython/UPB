# ui/SE/ui/canvas_widget.py - ПОЛНАЯ ФИНАЛЬНАЯ ВЕРСИЯ С ДЕЙКСТРОЙ И КЭШИРОВАНИЕМ

import math
import json
from typing import Dict, List, Optional, Any
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from ui.SE.core.models import Block, Connection, IfBlock


class CollapseButton(QGraphicsEllipseItem):
    """Кнопка сворачивания/разворачивания блока (+/-) внутри блока"""
    
    def __init__(self, parent_node):
        super().__init__(-8, -8, 16, 16, parent_node)
        self.parent_node = parent_node
        self.collapsed = False
        
        self.setBrush(QBrush(QColor("#3a3a3a")))
        self.setPen(QPen(QColor("#666666"), 1))
        self.setZValue(10)
        
        self.text = QGraphicsTextItem("−", self)
        self.text.setDefaultTextColor(QColor("#cccccc"))
        font = QFont("Arial", 10, QFont.Weight.Bold)
        self.text.setFont(font)
        self._center_text()
        
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
    
    def _center_text(self):
        text_rect = self.text.boundingRect()
        self.text.setPos(-text_rect.width() / 2, -text_rect.height() / 2)
    
    def set_collapsed(self, collapsed):
        self.collapsed = collapsed
        self.text.setPlainText("+" if collapsed else "−")
        self._center_text()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent_node.toggle_collapse()
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(QColor("#4a4a4a")))
        self.setPen(QPen(QColor("#888888"), 2))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(QColor("#3a3a3a")))
        self.setPen(QPen(QColor("#666666"), 1))
        super().hoverLeaveEvent(event)


class LightningEffectItem(QGraphicsObject):
    """Анимация молнии для появления блока"""
    
    def __init__(self, pos, color="#ff9900", parent=None):
        super().__init__(parent)
        self.setPos(pos)
        self._opacity = 0.0
        self._progress = 0.0
        self._finished = False
        self._color = QColor(color)
        
        self.timeline = QTimeLine(600)
        self.timeline.setFrameRange(0, 100)
        self.timeline.frameChanged.connect(self.update_animation)
        self.timeline.finished.connect(self.finish)
        self.timeline.start()
        
        self.setZValue(100)
        self._bounding_rect = QRectF(-150, -150, 300, 300)
    
    def update_animation(self, frame):
        self._progress = frame / 100.0
        self._opacity = 1.0 if self._progress < 0.25 else max(0, 1.0 - (self._progress - 0.25) / 0.35)
        self.prepareGeometryChange()
        self.update()
    
    def finish(self):
        self._finished = True
        self.hide()
        QTimer.singleShot(100, self.deleteLater)
    
    def boundingRect(self):
        return self._bounding_rect
    
    def paint(self, painter, option, widget):
        if self._finished or self._opacity < 0.01:
            return
        
        transform = painter.transform()
        zoom_level = max(abs(transform.m11()), abs(transform.m22()))
        
        painter.save()
        painter.resetTransform()
        
        scene_pos = self.scenePos()
        view = self.scene().views()[0] if self.scene() and self.scene().views() else None
        
        if view:
            view_pos = view.mapFromScene(scene_pos)
            center = view_pos
        else:
            center = QPointF(0, 0)
        
        painter.setOpacity(self._opacity)
        
        base_radius = 120
        radius = base_radius * zoom_level * (0.3 + 0.7 * self._progress)
        
        gradient = QRadialGradient(center, radius * 2)
        gradient.setColorAt(0, QColor(255, 255, 255, 200))
        gradient.setColorAt(0.1, QColor(200, 230, 255, 150))
        gradient.setColorAt(0.3, QColor(self._color).lighter(150))
        gradient.setColorAt(0.6, QColor(self._color))
        gradient.setColorAt(1, QColor(self._color).darker(200))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius * 2, radius * 2)
        
        core_radius = 50 * zoom_level * (0.3 + 0.7 * self._progress)
        core_gradient = QRadialGradient(center, core_radius)
        core_gradient.setColorAt(0, QColor(255, 255, 255, 255))
        core_gradient.setColorAt(0.5, QColor(255, 255, 200, 200))
        core_gradient.setColorAt(1, QColor(255, 200, 100, 100))
        
        painter.setBrush(QBrush(core_gradient))
        painter.drawEllipse(center, core_radius, core_radius)
        
        painter.setPen(QPen(QColor(255, 255, 255, int(150 * self._opacity)), 2 * zoom_level))
        for i in range(12):
            angle = i * math.pi / 6 + self._progress * 3
            length = (80 + 50 * math.sin(self._progress * 25 + i * 1.5)) * zoom_level
            x1 = center.x() + 40 * zoom_level * math.cos(angle)
            y1 = center.y() + 40 * zoom_level * math.sin(angle)
            x2 = center.x() + (40 * zoom_level + length) * math.cos(angle + 0.3 * math.sin(self._progress * 12 + i))
            y2 = center.y() + (40 * zoom_level + length) * math.sin(angle + 0.3 * math.sin(self._progress * 12 + i))
            
            points = [
                QPointF(x1, y1),
                QPointF((x1 + x2) / 2 + 25 * zoom_level * math.sin(angle + 1.5), (y1 + y2) / 2 + 25 * zoom_level * math.cos(angle + 1.5)),
                QPointF((x1 + x2) / 2 + 35 * zoom_level * math.sin(angle + 2.5), (y1 + y2) / 2 + 35 * zoom_level * math.cos(angle + 2.5)),
                QPointF(x2, y2)
            ]
            painter.drawPolyline(QPolygonF(points))
        
        for i in range(4):
            ring_radius = (50 + 80 * self._progress + i * 20) * zoom_level
            ring_alpha = int(100 * (1.0 - self._progress / 0.6) * self._opacity)
            if ring_alpha > 0:
                painter.setPen(QPen(QColor(200, 220, 255, ring_alpha), 2 * zoom_level))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(center, ring_radius, ring_radius)
        
        painter.setOpacity(1.0)
        painter.restore()


class PortItem(QGraphicsEllipseItem):
    """Порт для соединений"""
    
    def __init__(self, port_type, parent_node, size=8):
        super().__init__(-size/2, -size/2, size, size, parent_node)
        self.port_type = port_type
        self.parent_node = parent_node
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        
        if port_type == "input":
            self.default_brush = QBrush(QColor("#e74c3c"))
            self.highlight_brush = QBrush(QColor("#f1c40f"))
        elif port_type == "output":
            self.default_brush = QBrush(QColor("#2ecc71"))
            self.highlight_brush = QBrush(QColor("#f39c12"))
        elif port_type == "true":
            self.default_brush = QBrush(QColor("#2ecc71"))
            self.highlight_brush = QBrush(QColor("#f39c12"))
        elif port_type == "false":
            self.default_brush = QBrush(QColor("#e74c3c"))
            self.highlight_brush = QBrush(QColor("#f39c12"))
        else:
            self.default_brush = QBrush(QColor("#3498db"))
            self.highlight_brush = QBrush(QColor("#f1c40f"))
        
        self.setBrush(self.default_brush)
        self.setZValue(10)
        self.setData(0, port_type)

    def set_highlighted(self, highlighted):
        self.setBrush(self.highlight_brush if highlighted else self.default_brush)
    
    def hoverEnterEvent(self, event):
        self.setBrush(self.highlight_brush)
        self.setScale(1.3)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(self.default_brush)
        self.setScale(1.0)
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent_node.start_connection_drag(self.port_type)
            event.accept()
        else:
            super().mousePressEvent(event)


class SmartConnection(QGraphicsPathItem):
    """Умное соединение с обходом препятствий, анимированным пунктиром и подсветкой"""
    
    def __init__(self, connection, canvas, edge_type="data"):
        super().__init__()
        self.connection = connection
        self.canvas = canvas
        self.source = None
        self.destination = None
        self.source_port = connection.from_port
        self.dest_port = connection.to_port
        self.edge_type = edge_type
        
        self.original_edge = None
        self.source_child = None
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setZValue(-1)
        self.pen_width = 2
        self.setAcceptHoverEvents(True)
        
        if connection.from_port == "true":
            self.data_color = QColor("#2ecc71")
        elif connection.from_port == "false":
            self.data_color = QColor("#e74c3c")
        else:
            self.data_color = QColor("#3498db")
        
        self.inheritance_color = QColor("#9b59b6")
        self.proxy_color = QColor("#f39c12")
        
        self.grid_resolution = 30
        self.safety_margin = 15
        
        # Кэш для Дейкстры
        self._cached_path = None
        self._cached_obstacles_hash = None
        self._cached_start = None
        self._cached_end = None
        
        self._dash_offset = 0.0
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._update_animation)
        self._animation_timer.start(50)
        
        self._is_hovered = False
        self._hover_animation = 0.0
    
    def cleanup(self):
        if self._animation_timer:
            self._animation_timer.stop()
            self._animation_timer.deleteLater()
            self._animation_timer = None
    def update_path(self):
        """БЫСТРЫЙ A* вместо тяжелой Дейкстры"""
        if not hasattr(self, 'source_pos') or not hasattr(self, 'dest_pos'):
            return
        
        # Для "inheritance" и "proxy" рисуем прямую линию (им не нужен обход)
        if self.edge_type in ("inheritance", "proxy"):
            path_points = [self.source_pos, self.dest_pos]
        else:
            # Используем оптимизированный A* (с кэшированием)
            path_points = self._find_path_astar_fast(self.source_pos, self.dest_pos)
        
        path = QPainterPath()
        if path_points and len(path_points) >= 2:
            path.moveTo(path_points[0])
            
            if len(path_points) == 2:
                path.lineTo(path_points[1])
            else:
                # Плавные углы
                for i in range(1, len(path_points) - 1):
                    prev = path_points[i - 1]
                    curr = path_points[i]
                    next_pt = path_points[i + 1]
                    
                    dx1 = curr.x() - prev.x()
                    dy1 = curr.y() - prev.y()
                    dist1 = math.sqrt(dx1*dx1 + dy1*dy1)
                    
                    dx2 = next_pt.x() - curr.x()
                    dy2 = next_pt.y() - curr.y()
                    dist2 = math.sqrt(dx2*dx2 + dy2*dy2)
                    
                    corner_radius = min(15, dist1 * 0.3, dist2 * 0.3)
                    
                    if dist1 > 0 and dist2 > 0 and corner_radius > 1:
                        enter_x = curr.x() - (dx1 / dist1) * corner_radius
                        enter_y = curr.y() - (dy1 / dist1) * corner_radius
                        
                        exit_x = curr.x() + (dx2 / dist2) * corner_radius
                        exit_y = curr.y() + (dy2 / dist2) * corner_radius
                        
                        path.lineTo(enter_x, enter_y)
                        path.quadTo(curr, QPointF(exit_x, exit_y))
                    else:
                        path.lineTo(curr)
                
                path.lineTo(path_points[-1])
        
        self.setPath(path)
        self.update()
        
        if self.scene():
            self.scene().update()

    def _find_path_astar_fast(self, start, end):
        """СУПЕР-БЫСТРЫЙ A* с кэшированием и оптимизацией (замена Дейкстры)"""
        obstacles = self._get_obstacles()
        obstacles_hash = self._get_obstacles_hash(obstacles)
        
        # === КЭШ ===
        if (self._cached_path is not None and 
            self._cached_obstacles_hash == obstacles_hash and
            self._cached_start == start and 
            self._cached_end == end):
            return self._cached_path
        
        # === БЫСТРАЯ проверка прямой видимости ===
        if not obstacles or self._has_line_of_sight(start, end, obstacles):
            result = [start, end]
            self._save_cache(result, obstacles_hash, start, end)
            return result
        
        # === СОЗДАЕМ ГРАФ ВИДИМОСТИ (только вокруг препятствий) ===
        min_x = min(start.x(), end.x()) - 150
        max_x = max(start.x(), end.x()) + 150
        min_y = min(start.y(), end.y()) - 150
        max_y = max(start.y(), end.y()) + 150
        
        key_points = [start, end]
        
        # Добавляем углы препятствий как точки для обхода
        for obs in obstacles:
            # Проверяем, что препятствие пересекает область поиска
            if obs.right() < min_x or obs.left() > max_x or obs.bottom() < min_y or obs.top() > max_y:
                continue
                
            corners = [
                QPointF(obs.left() - 10, obs.top() - 10),
                QPointF(obs.right() + 10, obs.top() - 10),
                QPointF(obs.left() - 10, obs.bottom() + 10),
                QPointF(obs.right() + 10, obs.bottom() + 10)
            ]
            for corner in corners:
                if min_x <= corner.x() <= max_x and min_y <= corner.y() <= max_y:
                    if not self._is_point_in_obstacle(corner, obstacles):
                        key_points.append(corner)
        
        # Удаляем дубликаты
        seen = set()
        unique_points = []
        for p in key_points:
            key = (round(p.x(), 1), round(p.y(), 1))
            if key not in seen:
                seen.add(key)
                unique_points.append(p)
        key_points = unique_points
        
        # === A* АЛГОРИТМ (с эвристикой Манхэттен) ===
        n = len(key_points)
        if n < 2:
            result = [start, end]
            self._save_cache(result, obstacles_hash, start, end)
            return result
        
        start_idx = 0
        end_idx = 1
        
        def heuristic(p1, p2):
            # Манхэттенское расстояние (быстрее чем Евклид)
            return abs(p1.x() - p2.x()) + abs(p1.y() - p2.y())
        
        # Оптимизация: используем словари вместо списков для больших графов
        g_score = {i: float('inf') for i in range(n)}
        f_score = {i: float('inf') for i in range(n)}
        previous = {i: None for i in range(n)}
        
        g_score[start_idx] = 0
        f_score[start_idx] = heuristic(start, end)
        
        open_set = {start_idx}
        closed_set = set()
        
        while open_set:
            # Находим вершину с минимальным f_score (можно оптимизировать через heap)
            current = min(open_set, key=lambda x: f_score[x])
            
            if current == end_idx:
                # Восстанавливаем путь
                path = []
                while current is not None:
                    path.append(key_points[current])
                    current = previous[current]
                path.reverse()
                
                # Оптимизируем путь (убираем лишние точки)
                optimized = self._optimize_path(path, obstacles)
                self._save_cache(optimized, obstacles_hash, start, end)
                return optimized
            
            open_set.remove(current)
            closed_set.add(current)
            
            # Проверяем всех соседей (все видимые точки)
            for neighbor in range(n):
                if neighbor == current or neighbor in closed_set:
                    continue
                
                # Проверяем прямую видимость (быстрая проверка)
                if not self._has_line_of_sight(key_points[current], key_points[neighbor], obstacles):
                    continue
                
                # Расстояние (Евклид)
                dx = key_points[neighbor].x() - key_points[current].x()
                dy = key_points[neighbor].y() - key_points[current].y()
                dist = math.sqrt(dx*dx + dy*dy)
                
                tentative_g = g_score[current] + dist
                
                if tentative_g < g_score.get(neighbor, float('inf')):
                    previous[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(key_points[neighbor], end)
                    open_set.add(neighbor)
        
        # Путь не найден - прямая линия
        result = [start, end]
        self._save_cache(result, obstacles_hash, start, end)
        return result
    
    def _save_cache(self, path, obstacles_hash, start, end):
        """Сохраняем результат в кэш"""
        self._cached_path = path
        self._cached_obstacles_hash = obstacles_hash
        self._cached_start = start
        self._cached_end = end
    def _update_animation(self):
        try:
            if not self.scene():
                return
        except RuntimeError:
            return
        
        self._dash_offset += 2.0
        if self._dash_offset > 24:
            self._dash_offset = 0.0
        
        if self._is_hovered:
            self._hover_animation = min(1.0, self._hover_animation + 0.1)
        else:
            self._hover_animation = max(0.0, self._hover_animation - 0.1)
        
        try:
            self.update()
        except RuntimeError:
            pass
    
    def set_source(self, node):
        self.source = node
        self._cached_path = None
        self._cached_obstacles_hash = None
        self._cached_start = None
        self._cached_end = None
        self.update_position()
    
    def set_destination(self, node):
        self.destination = node
        self._cached_path = None
        self._cached_obstacles_hash = None
        self._cached_start = None
        self._cached_end = None
        self.update_position()
    
    def update_position(self):
        if self.source and self.destination:
            self.prepareGeometryChange()
            
            # Принудительно обновляем геометрию всех блоков
            if self.canvas:
                for node in self.canvas.nodes.values():
                    try:
                        node.prepareGeometryChange()
                    except RuntimeError:
                        pass
            
            source_point = self.source.get_port_position(self.source_port)
            dest_point = self.destination.get_port_position(self.dest_port)
            self.source_pos = source_point
            self.dest_pos = dest_point
            self.setPos(QPointF(0, 0))
            
            self._cached_path = None
            self._cached_obstacles_hash = None
            self._cached_start = None
            self._cached_end = None
            
            self.update_path()
            
            if self.scene():
                self.scene().update()
    
    def _get_obstacles(self):
        obstacles = []
        if self.canvas:
            for node in self.canvas.nodes.values():
                if node == self.source or node == self.destination:
                    continue
                
                node_rect = node.sceneBoundingRect()
                expanded_rect = node_rect.adjusted(
                    -self.safety_margin,
                    -self.safety_margin,
                    self.safety_margin,
                    self.safety_margin
                )
                obstacles.append(expanded_rect)
        return obstacles
    
    def _get_obstacles_hash(self, obstacles):
        hash_str = ""
        for obs in sorted(obstacles, key=lambda r: (r.x(), r.y())):
            hash_str += f"({obs.x():.1f},{obs.y():.1f},{obs.width():.1f},{obs.height():.1f})"
        return hash(hash_str)
    
    
    
    def _has_line_of_sight(self, p1, p2, obstacles):
        for obs in obstacles:
            if self._line_intersects_rect(p1, p2, obs):
                return False
        return True
    
    def _line_intersects_rect(self, p1, p2, rect):
        if rect.contains(p1) or rect.contains(p2):
            return True
        
        lines = [
            (QPointF(rect.left(), rect.top()), QPointF(rect.right(), rect.top())),
            (QPointF(rect.right(), rect.top()), QPointF(rect.right(), rect.bottom())),
            (QPointF(rect.right(), rect.bottom()), QPointF(rect.left(), rect.bottom())),
            (QPointF(rect.left(), rect.bottom()), QPointF(rect.left(), rect.top()))
        ]
        
        for l1, l2 in lines:
            if self._line_segments_intersect(p1, p2, l1, l2):
                return True
        
        return False
    
    def _line_segments_intersect(self, p1, p2, p3, p4):
        def cross_product(a, b):
            return a.x() * b.y() - a.y() * b.x()
        
        def subtract(a, b):
            return QPointF(a.x() - b.x(), a.y() - b.y())
        
        d1 = cross_product(subtract(p4, p3), subtract(p1, p3))
        d2 = cross_product(subtract(p4, p3), subtract(p2, p3))
        d3 = cross_product(subtract(p2, p1), subtract(p3, p1))
        d4 = cross_product(subtract(p2, p1), subtract(p4, p1))
        
        if ((d1 > 0 and d2 < 0) or (d1 < 0 and d2 > 0)) and \
           ((d3 > 0 and d4 < 0) or (d3 < 0 and d4 > 0)):
            return True
        
        return False
    
    def _is_point_in_obstacle(self, point, obstacles):
        for obs in obstacles:
            if obs.contains(point):
                return True
        return False
    
    def _optimize_path(self, path, obstacles):
        if len(path) <= 2:
            return path
        
        optimized = [path[0]]
        i = 0
        
        while i < len(path) - 1:
            furthest_visible = i + 1
            for j in range(i + 2, len(path)):
                if self._has_line_of_sight(path[i], path[j], obstacles):
                    furthest_visible = j
            
            optimized.append(path[furthest_visible])
            i = furthest_visible
        
        return optimized
    
    def hoverEnterEvent(self, event):
        self._is_hovered = True
        if self.source and self.destination:
            self.setToolTip(f"From: {self.source.block.name}\nTo: {self.destination.block.name}")
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self._is_hovered = False
        super().hoverLeaveEvent(event)
    
    def contextMenuEvent(self, event):
        menu = QMenu()
        
        delete_action = menu.addAction("🗑️ Delete connection")
        delete_action.triggered.connect(self.delete_connection)
        
        menu.addSeparator()
        
        info_action = menu.addAction(f"ID: {self.connection.id}")
        info_action.setEnabled(False)
        
        menu.exec(event.screenPos())
    
    def delete_connection(self):
        if self.canvas:
            self.canvas.remove_connection(self.connection.id)
    
    def paint(self, painter, option, widget=None):
        if not self.source or not self.destination:
            return
        
        painter.save()
        
        if self.edge_type == "inheritance":
            base_color = self.inheritance_color
        elif self.edge_type == "proxy":
            base_color = self.proxy_color
        else:
            base_color = self.data_color
        
        if self._hover_animation > 0:
            color = QColor(
                min(255, base_color.red() + int(50 * self._hover_animation)),
                min(255, base_color.green() + int(50 * self._hover_animation)),
                min(255, base_color.blue() + int(50 * self._hover_animation)),
                base_color.alpha()
            )
            glow_pen = QPen(color.lighter(150))
            glow_pen.setWidthF(self.pen_width * 3)
            glow_pen.setStyle(Qt.PenStyle.SolidLine)
            painter.setPen(glow_pen)
            painter.drawPath(self.path())
        else:
            color = base_color
        
        pen = QPen(color)
        pen.setWidth(self.pen_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setStyle(Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([10, 5])
        pen.setDashOffset(self._dash_offset)
        
        if widget:
            transform = painter.transform()
            zoom_level = max(abs(transform.m11()), abs(transform.m22()))
            pen.setWidthF(self.pen_width / zoom_level)
            pen.setDashOffset(self._dash_offset / zoom_level)
        
        painter.setPen(pen)
        painter.drawPath(self.path())
        
        if self.path().elementCount() > 1:
            last_point = self.path().currentPosition()
            
            prev_point = QPointF()
            elements = []
            for i in range(self.path().elementCount()):
                elem = self.path().elementAt(i)
                if elem.type in (QPainterPath.ElementType.MoveToElement, QPainterPath.ElementType.LineToElement):
                    elements.append(QPointF(elem.x, elem.y))
            
            if len(elements) >= 2:
                prev_point = elements[-2]
                
                arrow_size = 12
                arrow_width = 8
                
                if widget:
                    transform = painter.transform()
                    zoom_level = max(abs(transform.m11()), abs(transform.m22()))
                    arrow_size = 12 / zoom_level
                    arrow_width = 8 / zoom_level
                
                dx = last_point.x() - prev_point.x()
                dy = last_point.y() - prev_point.y()
                angle = math.atan2(dy, dx)
                
                p1 = last_point
                p2 = QPointF(
                    last_point.x() - arrow_size * math.cos(angle - math.pi/6),
                    last_point.y() - arrow_size * math.sin(angle - math.pi/6)
                )
                p3 = QPointF(
                    last_point.x() - arrow_size * math.cos(angle + math.pi/6),
                    last_point.y() - arrow_size * math.sin(angle + math.pi/6)
                )
                
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(color, 1))
                painter.drawPolygon(QPolygonF([p1, p2, p3]))
        
        painter.restore()


class GraphNode(QGraphicsRectItem):
    """Графическое представление блока на канвасе"""
    
    def __init__(self, block, canvas):
        super().__init__(QRectF(0, 0, block.size["width"], block.size["height"]))
        self.block = block
        self.canvas = canvas
        self.child_nodes = []
        self.parent_node = None
        self.collapsed = False
        
        self.ready_to_nest = False
        self.is_potential_parent = False
        self.dragged_node = None
        self.nest_animation_active = False
        self.last_mouse_pos = None
        self.potential_parent = None
        
        self.is_dragging_connection = False
        self.drag_start_port = None
        self.temp_connection_line = None
        self._dash_animation_timer = None
        self._dash_offset = 0.0
        self.hovered_port = None
        
        self._animations = {}
        self.hover_animation_id = None
        
        self.hover_check_timer = QTimer()
        self.hover_check_timer.setSingleShot(True)
        self.hover_check_timer.timeout.connect(self._check_nest_possibility)
        
        self._is_dragging = False
        self._drag_start_pos = None
        self._original_pos = None
        self._drag_start_time = None
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setAcceptDrops(True)
        self.setCacheMode(QGraphicsItem.CacheMode.NoCache)
        
        base_color = QColor(block.color)
        self.default_brush = QBrush(base_color)
        self.hover_brush = QBrush(base_color.lighter(120))
        self.drop_brush = QBrush(base_color.lighter(140))
        self.setBrush(self.default_brush)
        
        pen = QPen(QColor("#2c3e50"), 2)
        self.setPen(pen)
        self.setZValue(1)
        self._radius = 8
        
        self.external_connections = []
        self.proxy_edges = []
        
        self.text_item = QGraphicsTextItem(block.name, self)
        self.text_item.setDefaultTextColor(QColor("#ecf0f1"))
        font = QFont("Arial", 10, QFont.Weight.Bold)
        self.text_item.setFont(font)
        
        self.collapse_button = None
        if hasattr(block, 'children_ids') and block.children_ids:
            self._create_collapse_button()
        
        self._center_text()
        
        self.ports = {}
        self.create_ports()
        self.edges = []
        
        self.setPos(block.position["x"], block.position["y"])
    
    def _create_collapse_button(self):
        self.collapse_button = CollapseButton(self)
        self.collapse_button.setPos(self.rect().width() - 18, 8)
    
    def _center_text(self):
        text_rect = self.text_item.boundingRect()
        self.text_item.setPos(10, (self.rect().height() - text_rect.height()) / 2)
    
    def create_ports(self):
        rect = self.rect()
        port_size = 8
        
        input_port = PortItem("input", self, port_size)
        input_port.setBrush(QBrush(QColor("#e74c3c")))
        input_port.setPen(QPen(QColor("#c0392b"), 1))
        input_port.setPos(0, rect.height() / 2)
        input_port.setZValue(2)
        input_port.setData(0, "input")
        self.ports["input"] = input_port
        
        if self.block.node_type == "if":
            true_port = PortItem("true", self, port_size)
            true_port.setBrush(QBrush(QColor("#2ecc71")))
            true_port.setPen(QPen(QColor("#27ae60"), 1))
            true_port.setPos(rect.width(), rect.height() * 0.25)
            true_port.setZValue(2)
            true_port.setData(0, "true")
            self.ports["true"] = true_port
            
            false_port = PortItem("false", self, port_size)
            false_port.setBrush(QBrush(QColor("#e74c3c")))
            false_port.setPen(QPen(QColor("#c0392b"), 1))
            false_port.setPos(rect.width(), rect.height() * 0.75)
            false_port.setZValue(2)
            false_port.setData(0, "false")
            self.ports["false"] = false_port
        else:
            output_port = PortItem("output", self, port_size)
            output_port.setBrush(QBrush(QColor("#2ecc71")))
            output_port.setPen(QPen(QColor("#27ae60"), 1))
            output_port.setPos(rect.width(), rect.height() / 2)
            output_port.setZValue(2)
            output_port.setData(0, "output")
            self.ports["output"] = output_port

    def get_port_position(self, port_name):
        if port_name == "center":
            return self.scenePos() + QPointF(self.rect().width() / 2, self.rect().height() / 2)
        if port_name in self.ports:
            port = self.ports[port_name]
            return port.scenePos()
        return self.scenePos() + QPointF(self.rect().width() / 2, self.rect().height() / 2)
    
    def move_children(self, delta_x, delta_y):
        for child in self.child_nodes:
            new_pos = QPointF(child.pos().x() + delta_x, child.pos().y() + delta_y)
            child.setPos(new_pos)
            child.block.position["x"] = new_pos.x()
            child.block.position["y"] = new_pos.y()
            for edge in child.edges:
                edge.update_position()
            child.move_children(delta_x, delta_y)
    
    def start_connection_drag(self, port_name):
        print(f"🚀 [DRAG START] Port: {port_name} on '{self.block.name}'")
        
        self.is_dragging_connection = True
        self.drag_start_port = port_name
        
        if port_name in self.ports:
            self.ports[port_name].set_highlighted(True)
        
        self.grabMouse()
        
        temp_line = QGraphicsPathItem()
        temp_line.setZValue(1000)
        temp_line.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        temp_line.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        
        pen = QPen(QColor("#ffffff"), 2)
        pen.setStyle(Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([10, 5])
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        temp_line.setPen(pen)
        
        self.scene().addItem(temp_line)
        
        start_pos = self.get_port_position(port_name)
        path = QPainterPath()
        path.moveTo(start_pos)
        path.lineTo(start_pos)
        temp_line.setPath(path)
        
        self.temp_connection_line = temp_line
        self.temp_start_pos = start_pos
        
        self._dash_offset = 0.0
        if self._dash_animation_timer:
            self._dash_animation_timer.stop()
        self._dash_animation_timer = QTimer()
        self._dash_animation_timer.timeout.connect(self._animate_temp_dash)
        self._dash_animation_timer.start(50)
    
    def _animate_temp_dash(self):
        if not self.temp_connection_line or not self.is_dragging_connection:
            return
        
        try:
            self._dash_offset += 2.0
            if self._dash_offset > 24:
                self._dash_offset = 0.0
            
            pen = self.temp_connection_line.pen()
            pen.setDashOffset(self._dash_offset)
            self.temp_connection_line.setPen(pen)
        except RuntimeError:
            pass
    
    def update_temp_connection(self, pos):
        if not self.temp_connection_line or not self.drag_start_port:
            return
        
        try:
            start_pos = self.get_port_position(self.drag_start_port)
            
            path = QPainterPath()
            path.moveTo(start_pos)
            path.lineTo(pos)
            
            self.temp_connection_line.setPath(path)
        except RuntimeError:
            pass
    
    def cancel_connection_drag(self):
        print(f"❌ [DRAG CANCEL] Connection cancelled")
        
        self.is_dragging_connection = False
        self.drag_start_port = None
        
        try:
            self.ungrabMouse()
        except:
            pass
        
        if self._dash_animation_timer:
            self._dash_animation_timer.stop()
            self._dash_animation_timer.deleteLater()
            self._dash_animation_timer = None
        
        if self.temp_connection_line:
            try:
                if self.temp_connection_line.scene():
                    self.temp_connection_line.scene().removeItem(self.temp_connection_line)
            except RuntimeError:
                pass
            self.temp_connection_line = None
        
        for port in self.ports.values():
            port.set_highlighted(False)
    
    def finish_connection_drag(self, target_node, target_port):
        if not self.drag_start_port:
            return
        
        print(f"\n🔗 [CONNECTION] {self.block.name}[{self.drag_start_port}] → {target_node.block.name}[{target_port}]")
        
        if self.drag_start_port == "output" and target_port == "input":
            from_node, to_node = self, target_node
            from_port, to_port = "output", "input"
        else:
            self._update_status("❌ Only OUTPUT → INPUT allowed", is_warning=True)
            self.cancel_connection_drag()
            return
        
        if from_node == to_node:
            self._update_status("❌ Cannot connect to itself", is_warning=True)
            self.cancel_connection_drag()
            return
        
        for edge in self.canvas.edges.values():
            if (edge.source == from_node and edge.destination == to_node and
                edge.source_port == from_port and edge.dest_port == to_port):
                self._update_status("❌ Connection exists", is_warning=True)
                self.cancel_connection_drag()
                return
        
        connection = Connection(
            from_block_id=from_node.block.id,
            from_port=from_port,
            to_block_id=to_node.block.id,
            to_port=to_port,
            data_type="any"
        )
        
        if hasattr(self.canvas, 'parent_window') and hasattr(self.canvas.parent_window, 'project'):
            self.canvas.parent_window.project.add_connection(connection)
        
        edge = self.canvas.add_connection(connection, "data")
        if edge:
            self._update_status(f"✓ Connected {from_node.block.name} → {to_node.block.name}")
        
        self.cancel_connection_drag()
    
    def hoverMoveEvent(self, event):
        super().hoverMoveEvent(event)
        self.last_mouse_pos = event.pos()
        dragged_blocks = self._get_dragged_blocks()
        if self.is_dragging_connection:
            scene_pos = self.mapToScene(event.pos())
            self.update_temp_connection(scene_pos)
        if dragged_blocks:
            dragged_node = dragged_blocks[0]
            if dragged_node != self and not self._would_create_cycle(dragged_node):
                self.dragged_node = dragged_node
                self.is_potential_parent = True
                self._show_nest_opportunity(dragged_node)
                self.hover_check_timer.start(50)
            else:
                self._clear_nest_opportunity()
        else:
            self._clear_nest_opportunity()
    
    def hoverEnterEvent(self, event):
        super().hoverEnterEvent(event)
        self.setBrush(self.hover_brush)
        dragged_blocks = self._get_dragged_blocks()
        if dragged_blocks:
            self.hoverMoveEvent(event)
    
    def hoverLeaveEvent(self, event):
        super().hoverLeaveEvent(event)
        self.setBrush(self.default_brush)
        self._clear_nest_opportunity()
        self.last_mouse_pos = None
    
    def _get_dragged_blocks(self):
        dragged = []
        if self.scene():
            for item in self.scene().items():
                if isinstance(item, GraphNode) and item._is_dragging:
                    dragged.append(item)
        return dragged
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            for port_name, port in self.ports.items():
                port_scene_pos = port.scenePos()
                mouse_scene_pos = self.mapToScene(pos)
                port_rect = QRectF(port_scene_pos.x() - 4, port_scene_pos.y() - 4, 8, 8)
                if port_rect.contains(mouse_scene_pos):
                    self.start_connection_drag(port_name)
                    event.accept()
                    return
            self._is_dragging = False
            self._drag_start_pos = event.pos()
            self._original_pos = self.pos()
            self._drag_start_time = QTime.currentTime()
            modifiers = QApplication.keyboardModifiers()
            if not (modifiers & (Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.ControlModifier)):
                if self.scene():
                    for item in self.scene().selectedItems():
                        item.setSelected(False)
            self.setSelected(True)
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.is_dragging_connection:
            scene_pos = event.scenePos()
            self.update_temp_connection(scene_pos)
            event.accept()
            return
        
        if event.buttons() & Qt.MouseButton.LeftButton:
            if not self._is_dragging and self._drag_start_pos:
                move_distance = (event.pos() - self._drag_start_pos).manhattanLength()
                if move_distance > QApplication.startDragDistance():
                    self._is_dragging = True
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_dragging_connection:
                scene_pos = event.scenePos()
                items = self.scene().items(scene_pos)
                
                target_port = None
                target_node = None
                
                for item in items:
                    if isinstance(item, PortItem) and item.parent_node != self:
                        target_port = item
                        target_node = item.parent_node
                        break
                    elif isinstance(item, GraphNode) and item != self:
                        target_node = item
                        if self.drag_start_port == "output" and "input" in item.ports:
                            target_port = item.ports["input"]
                        break
                
                if target_port and target_node:
                    self.finish_connection_drag(target_node, target_port.port_type)
                elif target_node and self.drag_start_port == "output" and "input" in target_node.ports:
                    self.finish_connection_drag(target_node, "input")
                else:
                    self.cancel_connection_drag()
                
                event.accept()
                return
            
            if self._is_dragging:
                new_pos = self.pos()
                if self._original_pos and self._original_pos != new_pos:
                    self.block.position["x"] = new_pos.x()
                    self.block.position["y"] = new_pos.y()
                    
                    for edge in self.edges:
                        edge.update_position()
                    
                    self._try_nest_at_release()
                    self._auto_save()
                
                self._is_dragging = False
                self.ready_to_nest = False
                self.potential_parent = None
                self.setBrush(self.default_brush)
                self.setScale(1.0)
            
            self._drag_start_pos = None
            self._original_pos = None
            self._drag_start_time = None
            
        super().mouseReleaseEvent(event)
    
    def _show_nest_opportunity(self, dragged_node):
        if not self.nest_animation_active:
            self._start_nest_animation(dragged_node)
    
    def _clear_nest_opportunity(self):
        self.is_potential_parent = False
        self._stop_nest_animation()
        self.setBrush(self.default_brush)
        self.setToolTip("")
        if hasattr(self, 'dragged_node') and self.dragged_node:
            self.dragged_node.potential_parent = None
            self.dragged_node.ready_to_nest = False
            self.dragged_node = None
    
    def _check_nest_possibility(self):
        if self.is_potential_parent and self.dragged_node and self.last_mouse_pos:
            if self.contains(self.last_mouse_pos):
                self.setBrush(self.drop_brush)
                self.setScale(1.05)
            else:
                self._clear_nest_opportunity()
    
    def _start_nest_animation(self, dragged_node):
        self.nest_animation_active = True
        anim = QVariantAnimation()
        anim.setDuration(1000)
        anim.setStartValue(1.0)
        anim.setKeyValueAt(0.5, 1.1)
        anim.setEndValue(1.0)
        anim.setLoopCount(-1)
        anim.valueChanged.connect(self._update_hover_scale)
        self.hover_animation_id = id(anim)
        self._animations[self.hover_animation_id] = anim
        anim.start()
    
    def _stop_nest_animation(self):
        self.nest_animation_active = False
        if self.hover_animation_id:
            if self.hover_animation_id in self._animations:
                anim = self._animations[self.hover_animation_id]
                anim.stop()
                del self._animations[self.hover_animation_id]
            self.hover_animation_id = None
        self.setScale(1.0)
    
    def _update_hover_scale(self, value):
        self.setScale(value)
    
    def _try_nest_at_release(self):
        if self.scene():
            items = self.scene().items(self.pos())
            for item in items:
                if isinstance(item, GraphNode) and item != self:
                    if item.is_potential_parent and not self._would_create_cycle(item):
                        distance = (self.pos() - item.pos()).manhattanLength()
                        if distance < 200:
                            self.canvas.nest_block(self, item)
                            item._clear_nest_opportunity()
                            break
    
    def _would_create_cycle(self, child_node):
        current = child_node
        while current:
            if current == self:
                return True
            current = current.parent_node
        return False
    
    def contains(self, point):
        return self.rect().contains(point)
    
    def add_child(self, child_node):
        if child_node not in self.child_nodes:
            self.child_nodes.append(child_node)
            child_node.parent_node = self
            if child_node.block.id not in self.block.children_ids:
                self.block.children_ids.append(child_node.block.id)
            if child_node.block.parent_id != self.block.id:
                child_node.block.parent_id = self.block.id
            if not self.collapse_button and len(self.child_nodes) > 0:
                self._create_collapse_button()
                self._center_text()
    
    def remove_child(self, child_node):
        if child_node in self.child_nodes:
            self.child_nodes.remove(child_node)
            child_node.parent_node = None
            if child_node.block.id in self.block.children_ids:
                self.block.children_ids.remove(child_node.block.id)
    
    def toggle_collapse(self):
        self.collapsed = not self.collapsed
        if self.collapse_button:
            self.collapse_button.set_collapsed(self.collapsed)
        self.canvas.update_connections()
        self.update()
    
    def contextMenuEvent(self, event):
        menu = QMenu()
        
        selected_nodes = [item for item in self.scene().selectedItems() 
                        if isinstance(item, GraphNode)]
        
        if len(selected_nodes) > 1:
            title_action = menu.addAction(f"📦 Selected: {len(selected_nodes)} blocks")
            title_action.setEnabled(False)
            menu.addSeparator()
            
            delete_action = menu.addAction("🗑️ Delete Selected Blocks")
            delete_action.setShortcut(QKeySequence(Qt.Key.Key_Delete))
            delete_action.triggered.connect(self.canvas.delete_selected_blocks)
            
            copy_action = menu.addAction("📋 Copy Selected Blocks")
            copy_action.setShortcut(QKeySequence.StandardKey.Copy)
            copy_action.triggered.connect(lambda: self.canvas.copy_selected_blocks())
            
            menu.addAction(delete_action)
            menu.addSeparator()
            menu.addAction(copy_action)
        else:
            title_action = menu.addAction(f"Block: {self.block.name}")
            title_action.setEnabled(False)
            menu.addSeparator()
            
            rename_action = menu.addAction("✏️ Rename")
            rename_action.setShortcut(QKeySequence(Qt.Key.Key_F2))
            rename_action.triggered.connect(self._rename_block)
            
            duplicate_action = menu.addAction("📋 Duplicate")
            duplicate_action.setShortcut(QKeySequence.StandardKey.Copy)
            duplicate_action.triggered.connect(self._duplicate_block)
            
            delete_action = menu.addAction("🗑️ Delete")
            delete_action.setShortcut(QKeySequence(Qt.Key.Key_Delete))
            delete_action.triggered.connect(lambda: self.canvas.remove_block_with_animation(self.block.id))
            
            menu.addAction(rename_action)
            menu.addAction(duplicate_action)
            menu.addAction(delete_action)
            
            if self.parent_node:
                menu.addSeparator()
                exit_action = menu.addAction(f"📤 Exit from '{self.parent_node.block.name}'")
                exit_action.triggered.connect(self.remove_from_parent)
                menu.addAction(exit_action)
            
            menu.addSeparator()
            connections_count = len(self.edges) + len(self.external_connections)
            info_action = menu.addAction(f"ℹ️ Connections: {connections_count}")
            info_action.setEnabled(False)
        
        if hasattr(self.canvas, 'clipboard_blocks') and self.canvas.clipboard_blocks:
            menu.addSeparator()
            paste_action = menu.addAction("📌 Paste Blocks")
            paste_action.setShortcut(QKeySequence.StandardKey.Paste)
            paste_action.triggered.connect(lambda: self.canvas.paste_blocks(event.scenePos()))
        
        menu.exec(event.screenPos())
    
    def _rename_block(self):
        new_name, ok = QInputDialog.getText(None, "Rename Block", "Enter new name:", text=self.block.name)
        if ok and new_name:
            self.block.name = new_name
            self.text_item.setPlainText(new_name)
            self._center_text()
            if hasattr(self.canvas.parent_window, 'auto_save_project'):
                self.canvas.parent_window.auto_save_project()
    
    def _duplicate_block(self):
        new_x = self.pos().x() + 50
        new_y = self.pos().y() + 50
        
        new_node = self.canvas.add_block_with_animation(
            self.block.node_type,
            f"{self.block.name} (copy)",
            new_x,
            new_y,
            self.block.color
        )
        
        if new_node and self.block.params:
            new_node.block.params = self.block.params.copy()
        
        if new_node:
            self.scene().clearSelection()
            new_node.setSelected(True)
    
    def _delete_block(self):
        reply = QMessageBox.question(None, "Delete Block", f"Delete '{self.block.name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.canvas.remove_block_with_animation(self.block.id)
    
    def remove_from_parent(self):
        if self.parent_node:
            self.parent_node.remove_child(self)
            self.block.parent_id = None
            self.canvas.remove_block(self.block.id)
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            if self._is_dragging:
                new_pos = value
                old_pos = self.pos()
                delta_x = new_pos.x() - old_pos.x()
                delta_y = new_pos.y() - old_pos.y()
                
                self.block.position["x"] = new_pos.x()
                self.block.position["y"] = new_pos.y()
                
                # Обновляем ВСЕ соединения - движущийся блок влияет на все пути
                for edge_id, edge in list(self.canvas.edges.items()):
                    try:
                        if edge.scene():
                            edge._cached_path = None
                            edge._cached_obstacles_hash = None
                            edge._cached_start = None
                            edge._cached_end = None
                            edge.update_position()
                    except RuntimeError:
                        pass
                
                if self.child_nodes and (abs(delta_x) > 0 or abs(delta_y) > 0):
                    self.move_children(delta_x, delta_y)
                
                return new_pos
                
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            if value and self.scene():
                if hasattr(self.canvas, 'parent_window'):
                    main_window = self.canvas.parent_window
                    if hasattr(main_window, 'property_editor'):
                        main_window.property_editor.set_block(self.block)
                        
        return super().itemChange(change, value)
    
    def paint(self, painter, option, widget=None):
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        path = QPainterPath()
        path.addRoundedRect(self.rect(), self._radius, self._radius)
        painter.drawPath(path)
        
        if self.isSelected():
            painter.setPen(QPen(QColor("#f39c12"), 3))
            painter.drawRoundedRect(self.rect().adjusted(-2, -2, 2, 2), self._radius + 2, self._radius + 2)
    
    def add_edge(self, edge):
        if edge not in self.edges:
            self.edges.append(edge)
    
    def remove_edge(self, edge):
        if edge in self.edges:
            self.edges.remove(edge)
    
    def _auto_save(self):
        try:
            if self.canvas and hasattr(self.canvas, 'parent_window'):
                main_window = self.canvas.parent_window
                if hasattr(main_window, 'auto_save_project'):
                    main_window.auto_save_project()
        except Exception:
            pass
    
    def _update_status(self, message, is_warning=False):
        if self.canvas and hasattr(self.canvas, '_update_status'):
            self.canvas._update_status(message, is_warning)


class CanvasWidget(QGraphicsView):
    """Виджет канваса с поддержкой соединений, горячих клавиш и анимаций"""
    
    block_selected = Signal(object)
    block_double_clicked = Signal(object)
    
    def __init__(self):
        super().__init__()
        
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-1000000, -1000000, 2000000, 2000000)
        self.setScene(self.scene)
        
        self.nodes: Dict[int, GraphNode] = {}
        self.edges: Dict[str, SmartConnection] = {}
        self.next_id = 1
        
        self.grid_enabled = True
        self.zoom_factor = 1.0
        self.zoom_min = 0.1
        self.zoom_max = 5.0
        self.zoom_step = 1.1
        self._mouse_scene_pos = None
        
        self.grid_spacing = 60
        self.grid_dot_radius = 4
        self.repel_radius = 250
        
        self._grid_points = {}
        self._grid_velocities = {}
        self._visible_rect = QRectF()
        
        self.parent_window = None
        self._is_panning = False
        self._last_pan_pos = None
        self._dragging_block = False
        self._move_step = 20
        
        self.clipboard_blocks = []
        self._active_animations = []
        
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setAcceptDrops(True)
        self.viewport().setAcceptDrops(True)
        
        self.setBackgroundBrush(QBrush(QColor("#0a0a1a")))
        self.setMinimumSize(400, 300)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        self.scene.selectionChanged.connect(self.on_selection_changed)
        
        self.grid_update_timer = QTimer()
        self.grid_update_timer.timeout.connect(self.update_grid_animation)
        self.grid_update_timer.start(16)
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_nest_states)
        self.update_timer.start(50)
        
        self.status_label = None
    
    def _get_key(self, x, y):
        return f"{int(x)}_{int(y)}"
    
    def _update_visible_points(self, rect):
        max_displacement = self.repel_radius * 2
        padding = max(200, max_displacement)
        
        visible_rect = rect.adjusted(-padding, -padding, padding, padding)
        
        if self._visible_rect == visible_rect:
            return
        
        self._visible_rect = visible_rect
        
        spacing = self.grid_spacing / self.zoom_factor
        spacing = max(10, min(100, spacing))
        
        left = int(visible_rect.left()) - (int(visible_rect.left()) % spacing) - spacing
        top = int(visible_rect.top()) - (int(visible_rect.top()) % spacing) - spacing
        right = int(visible_rect.right()) + spacing
        bottom = int(visible_rect.bottom()) + spacing
        
        new_points = {}
        new_velocities = {}
        
        x = left
        while x <= right:
            y = top
            while y <= bottom:
                key = self._get_key(x, y)
                if key in self._grid_points:
                    new_points[key] = self._grid_points[key][:]
                    new_velocities[key] = self._grid_velocities[key][:]
                else:
                    new_points[key] = [x, y]
                    new_velocities[key] = [0.0, 0.0]
                y += spacing
            x += spacing
        
        self._grid_points = new_points
        self._grid_velocities = new_velocities
    
    def update_grid_animation(self):
        if not self.grid_enabled:
            return
        
        needs_update = False
        for key, point in self._grid_points.items():
            orig_x = int(key.split('_')[0])
            orig_y = int(key.split('_')[1])
            if abs(point[0] - orig_x) > 0.5 or abs(point[1] - orig_y) > 0.5:
                needs_update = True
                break
        
        if not needs_update:
            for key, vel in self._grid_velocities.items():
                if abs(vel[0]) > 0.001 or abs(vel[1]) > 0.001:
                    needs_update = True
                    break
        
        if needs_update:
            self.viewport().update()
    
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        
        if not self.grid_enabled:
            return
        
        if not self._mouse_scene_pos:
            self._mouse_scene_pos = QPointF(0, 0)
        
        self._update_physics_for_all_points()
        self._update_visible_points(rect)
        
        if not self._grid_points:
            return
        
        transform = painter.transform()
        zoom_level = max(abs(transform.m11()), abs(transform.m22()))
        
        dot_size = self.grid_dot_radius / zoom_level
        dot_size = max(0.5, min(8, dot_size))
        
        mouse_x = self._mouse_scene_pos.x()
        mouse_y = self._mouse_scene_pos.y()
        
        repel_radius = self.repel_radius / zoom_level
        repel_radius = max(50, min(500, repel_radius))
        
        for key, point in list(self._grid_points.items()):
            px, py = point[0], point[1]
            
            if not rect.contains(px, py):
                continue
            
            dx = px - mouse_x
            dy = py - mouse_y
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist < repel_radius:
                t = 1.0 - (dist / repel_radius)
                alpha = 200 + int(55 * t)
                color = QColor(160, 216, 255, alpha)
                current_dot_size = dot_size * (1.0 + 0.5 * t)
            else:
                color = QColor(100, 180, 255, 80)
                current_dot_size = dot_size
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(px, py), current_dot_size, current_dot_size)
            
            if dist < repel_radius * 0.5:
                center_size = current_dot_size * 0.4
                painter.setBrush(QBrush(QColor(255, 255, 255, 150)))
                painter.drawEllipse(QPointF(px, py), center_size, center_size)
    
    def _update_physics_for_all_points(self):
        if not self._mouse_scene_pos or not self._grid_points:
            return
        
        zoom_level = self.zoom_factor
        mouse_x = self._mouse_scene_pos.x()
        mouse_y = self._mouse_scene_pos.y()
        
        repel_radius = self.repel_radius / max(0.5, min(2.0, zoom_level))
        repel_radius = max(50, min(500, repel_radius))
        
        speed_scale = 1.0 / max(0.5, min(2.0, zoom_level))
        max_velocity = 15.0 * speed_scale
        
        for key, point in self._grid_points.items():
            px, py = point[0], point[1]
            
            dx = px - mouse_x
            dy = py - mouse_y
            dist = math.sqrt(dx*dx + dy*dy)
            
            velocity = self._grid_velocities.get(key, [0.0, 0.0])
            vx, vy = velocity[0], velocity[1]
            
            if dist < repel_radius and dist > 1:
                angle = math.atan2(dy, dx)
                force = min(10.0, 3.0 * (1 - dist / repel_radius) ** 3 * speed_scale)
                vx += math.cos(angle) * force
                vy += math.sin(angle) * force
            
            orig_x = int(key.split('_')[0])
            orig_y = int(key.split('_')[1])
            
            return_dx = orig_x - px
            return_dy = orig_y - py
            return_dist = math.sqrt(return_dx*return_dx + return_dy*return_dy)
            
            if return_dist > 0.5:
                norm_x = return_dx / return_dist
                norm_y = return_dy / return_dist
                return_force = min(5.0, 0.25 * speed_scale * min(return_dist / 30, 5.0))
                vx += norm_x * return_force
                vy += norm_y * return_force
            
            current_speed = math.sqrt(vx*vx + vy*vy)
            if current_speed > max_velocity:
                vx = (vx / current_speed) * max_velocity
                vy = (vy / current_speed) * max_velocity
            
            if zoom_level < 1.0:
                damping = 0.85
            else:
                damping = 0.92
            
            vx *= damping
            vy *= damping
            
            new_x = px + vx * speed_scale
            new_y = py + vy * speed_scale
            
            speed = math.sqrt(vx*vx + vy*vy)
            if speed < 0.001 and return_dist < 0.5:
                vx = 0
                vy = 0
                new_x = orig_x
                new_y = orig_y
            
            self._grid_velocities[key] = [vx, vy]
            self._grid_points[key] = [new_x, new_y]
    
    def add_block_with_animation(self, node_type: str, name: str, x: float, y: float, color: str = "#3498db"):
        node = self.add_block_from_data(node_type, name, x, y, color)
        
        if node:
            node.setOpacity(1.0)
            node.setScale(1.0)
            node.setPos(x, y)
            self.scene.update()
            self.viewport().update()
        
        return node
    
    def add_block_from_data(self, node_type: str, name: str, x: float = 0, y: float = 0, color: str = "#3498db"):
        from ui.SE.core.models import Block
        
        try:
            block = Block(
                block_id=self.next_id,
                node_type=node_type,
                name=name,
                x=x,
                y=y,
                color=color
            )
            block.params = block.get_default_params()
            
            node = GraphNode(block, self)
            self.scene.addItem(node)
            self.nodes[block.id] = node
            self.next_id += 1
            
            self.scene.clearSelection()
            node.setSelected(True)
            self.block_selected.emit(node)
            
            self.scene.update()
            self.viewport().update()
            
            return node
            
        except Exception as e:
            print(f"❌ [CANVAS] Error adding block: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def remove_block_with_animation(self, block_id: int):
        if block_id not in self.nodes:
            return False
        
        node = self.nodes[block_id]
        
        timeline = QTimeLine(400)
        timeline.setFrameRange(0, 100)
        
        self._active_animations.append(timeline)
        
        def update_anim(frame):
            value = frame / 100.0
            node.setOpacity(1.0 - value)
            node.setScale(1.0 - 0.7 * value)
            node.setPos(node.pos().x(), node.pos().y() + 5 * value)
            self.viewport().update()
        
        def finish_anim():
            self.remove_block(block_id)
            self.scene.update()
            self.viewport().update()
            if timeline in self._active_animations:
                self._active_animations.remove(timeline)
        
        timeline.frameChanged.connect(update_anim)
        timeline.finished.connect(finish_anim)
        timeline.start()
        
        return True
    
    def remove_block(self, block_id):
        if block_id in self.nodes:
            node = self.nodes[block_id]
            
            edges_to_remove = []
            for edge_id, edge in self.edges.items():
                if edge.source == node or edge.destination == node:
                    edges_to_remove.append(edge_id)
            
            for edge_id in edges_to_remove:
                edge = self.edges[edge_id]
                if hasattr(edge, 'cleanup'):
                    edge.cleanup()
                if hasattr(edge, '_animation_timer') and edge._animation_timer:
                    edge._animation_timer.stop()
                    edge._animation_timer.deleteLater()
                if edge.source:
                    edge.source.remove_edge(edge)
                if edge.destination:
                    edge.destination.remove_edge(edge)
                self.scene.removeItem(edge)
                del self.edges[edge_id]
            
            if node.parent_node:
                node.parent_node.remove_child(node)
            
            for child in node.child_nodes[:]:
                self.remove_block(child.block.id)
            
            self.scene.removeItem(node)
            del self.nodes[block_id]
            
            self.scene.update()
            self.viewport().update()
            
            return True
        return False
    
    def delete_selected_blocks(self):
        selected_items = self.scene.selectedItems()
        blocks_to_delete = [item for item in selected_items if isinstance(item, GraphNode)]
        
        if not blocks_to_delete:
            return False
        
        if len(blocks_to_delete) > 1:
            reply = QMessageBox.question(
                None, "Delete Blocks",
                f"Delete {len(blocks_to_delete)} selected blocks?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return False
        
        for node in blocks_to_delete:
            self.remove_block_with_animation(node.block.id)
        
        self.block_selected.emit(None)
        self.scene.update()
        self.viewport().update()
        return True
    
    def copy_selected_blocks(self):
        selected_nodes = [item for item in self.scene.selectedItems() 
                        if isinstance(item, GraphNode)]
        
        if not selected_nodes:
            self._update_status("No blocks selected for copy", is_warning=True)
            return
        
        self.clipboard_blocks = []
        for node in selected_nodes:
            block_data = {
                'type': node.block.node_type,
                'name': node.block.name,
                'color': node.block.color,
                'params': node.block.params.copy() if node.block.params else {},
                'x': node.pos().x(),
                'y': node.pos().y()
            }
            self.clipboard_blocks.append(block_data)
        
        self._update_status(f"📋 Copied {len(selected_nodes)} blocks")
    
    def paste_blocks(self, position=None):
        if not self.clipboard_blocks:
            self._update_status("Clipboard is empty", is_warning=True)
            return
        
        if position is None:
            center = self.mapToScene(self.viewport().rect().center())
            position = QPointF(center.x() + 50, center.y() + 50)
        
        if self.clipboard_blocks:
            avg_x = sum(b['x'] for b in self.clipboard_blocks) / len(self.clipboard_blocks)
            avg_y = sum(b['y'] for b in self.clipboard_blocks) / len(self.clipboard_blocks)
        else:
            avg_x, avg_y = 0, 0
        
        offset_x = position.x() - avg_x
        offset_y = position.y() - avg_y
        
        new_nodes = []
        for block_data in self.clipboard_blocks:
            new_x = block_data['x'] + offset_x
            new_y = block_data['y'] + offset_y
            
            node = self.add_block_with_animation(
                block_data['type'],
                f"{block_data['name']} (copy)",
                new_x,
                new_y,
                block_data['color']
            )
            
            if node and block_data['params']:
                node.block.params = block_data['params']
            
            if node:
                new_nodes.append(node)
        
        self.scene.clearSelection()
        for node in new_nodes:
            node.setSelected(True)
        
        self._update_status(f"📌 Pasted {len(new_nodes)} blocks")
        
        return new_nodes
    
    def add_connection(self, connection, connection_type="data"):
        edge = SmartConnection(connection, self, connection_type)
        from_node = self.nodes.get(connection.from_block_id)
        to_node = self.nodes.get(connection.to_block_id)
        if from_node and to_node:
            edge.set_source(from_node)
            edge.set_destination(to_node)
            self.scene.addItem(edge)
            self.edges[connection.id] = edge
            if connection_type != "proxy":
                from_node.add_edge(edge)
                to_node.add_edge(edge)
            self.scene.update()
            self.viewport().update()
            return edge
        return None
    
    def remove_connection(self, connection_id):
        if connection_id in self.edges:
            edge = self.edges[connection_id]
            
            if hasattr(edge, 'cleanup'):
                edge.cleanup()
            
            if edge.source:
                edge.source.remove_edge(edge)
            if edge.destination:
                edge.destination.remove_edge(edge)
            self.scene.removeItem(edge)
            del self.edges[connection_id]
            self.scene.update()
            self.viewport().update()
            return True
        return False
    
    def update_connections(self):
        for edge in list(self.edges.values()):
            try:
                if edge.scene():
                    edge._cached_path = None
                    edge._cached_obstacles_hash = None
                    edge._cached_start = None
                    edge._cached_end = None
                    edge.update_position()
            except RuntimeError:
                pass
        self.scene.update()
        self.viewport().update()
    
    def update_all_connections(self):
        """МАССОВОЕ обновление всех соединений (вызывается при изменениях)"""
        # Сбрасываем кэш у всех соединений
        for edge in self.edges.values():
            if hasattr(edge, '_cached_path'):
                edge._cached_path = None
                edge._cached_obstacles_hash = None
                edge._cached_start = None
                edge._cached_end = None
            edge.update_position()
        
        self.scene.update()
        self.viewport().update()

    def nest_block(self, child_node, parent_node):
        if child_node == parent_node:
            return False
        if child_node._would_create_cycle(parent_node):
            return False
        if child_node.parent_node:
            child_node.parent_node.remove_child(child_node)
        parent_node.add_child(child_node)
        child_node.setPos(parent_node.pos().x() + 50, parent_node.pos().y() + 50)
        child_node.block.parent_id = parent_node.block.id
        if child_node.block.id not in parent_node.block.children_ids:
            parent_node.block.children_ids.append(child_node.block.id)
        
        from ui.SE.core.models import Connection
        conn = Connection(
            from_block_id=parent_node.block.id,
            from_port="center",
            to_block_id=child_node.block.id,
            to_port="center",
            data_type="inheritance"
        )
        self.add_connection(conn, "inheritance")
        
        self.scene.update()
        self.viewport().update()
        
        if hasattr(self.parent_window, 'auto_save_project'):
            self.parent_window.auto_save_project()
        return True
    
    def get_all_blocks(self):
        return list(self.nodes.values())
    
    def clear(self):
        # Очищаем все таймеры соединений
        for edge in self.edges.values():
            if hasattr(edge, 'cleanup'):
                edge.cleanup()
        self.nodes.clear()
        self.edges.clear()
        self.scene.clear()
        self.next_id = 1
        self._grid_points.clear()
        self._grid_velocities.clear()
        self._visible_rect = QRectF()
        self.scene.update()
        self.viewport().update()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected_blocks()
            event.accept()
            return
        
        if event.key() == Qt.Key.Key_A and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            for node in self.nodes.values():
                node.setSelected(True)
            event.accept()
            return
        
        if event.key() == Qt.Key.Key_C and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.copy_selected_blocks()
            event.accept()
            return
        
        if event.key() == Qt.Key.Key_V and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.paste_blocks()
            event.accept()
            return
        
        if event.key() == Qt.Key.Key_D and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            selected = [item for item in self.scene.selectedItems() if isinstance(item, GraphNode)]
            if selected:
                self.copy_selected_blocks()
                self.paste_blocks()
            event.accept()
            return
        
        if event.key() == Qt.Key.Key_Escape:
            for node in self.nodes.values():
                node.setSelected(False)
            for edge in self.edges.values():
                edge.setSelected(False)
            event.accept()
            return
        
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            step = self._move_step
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                step = 5
            
            dx, dy = 0, 0
            if event.key() == Qt.Key.Key_Right:
                dx = step
            elif event.key() == Qt.Key.Key_Left:
                dx = -step
            elif event.key() == Qt.Key.Key_Up:
                dy = -step
            elif event.key() == Qt.Key.Key_Down:
                dy = step
            else:
                super().keyPressEvent(event)
                return
            
            if dx != 0 or dy != 0:
                self.move_selected_nodes(dx, dy)
                event.accept()
                return
        
        super().keyPressEvent(event)
    
    def move_selected_nodes(self, dx: float, dy: float):
        selected_nodes = [node for node in self.nodes.values() if node.isSelected()]
        if not selected_nodes:
            return
        
        for node in selected_nodes:
            new_pos = node.pos() + QPointF(dx, dy)
            node.setPos(new_pos)
            node.block.position["x"] = new_pos.x()
            node.block.position["y"] = new_pos.y()
            for edge in node.edges:
                edge.update_position()
            if node.child_nodes:
                node.move_children(dx, dy)
        
        if hasattr(self.parent_window, 'auto_save_project'):
            self.parent_window.auto_save_project()
    
    def on_selection_changed(self):
        try:
            selected_items = self.scene.selectedItems()
            if selected_items:
                for item in selected_items:
                    if isinstance(item, GraphNode) and item.block:
                        self.block_selected.emit(item)
                        break
        except Exception as e:
            print(f"Error in on_selection_changed: {e}")
    
    def select_block(self, block_id):
        if block_id in self.nodes:
            node = self.nodes[block_id]
            node.setSelected(True)
            self.centerOn(node)
    
    def update_nest_states(self):
        dragged_blocks = []
        for node in self.nodes.values():
            if node._is_dragging:
                dragged_blocks.append(node)
        if dragged_blocks:
            global_pos = QCursor.pos()
            view_pos = self.mapFromGlobal(global_pos)
            scene_pos = self.mapToScene(view_pos)
            items = self.scene.items(scene_pos)
            for node in self.nodes.values():
                was_potential = node.is_potential_parent
                node.is_potential_parent = False
                if node in items and node != dragged_blocks[0]:
                    if not node._would_create_cycle(dragged_blocks[0]):
                        node.is_potential_parent = True
                        node.dragged_node = dragged_blocks[0]
                        if not was_potential:
                            node._show_nest_opportunity(dragged_blocks[0])
                    else:
                        if was_potential:
                            node._clear_nest_opportunity()
                else:
                    if was_potential:
                        node._clear_nest_opportunity()
        else:
            for node in self.nodes.values():
                if node.is_potential_parent:
                    node._clear_nest_opportunity()
    
    def _update_status(self, message: str, is_warning: bool = False):
        try:
            if not message or message.strip() == "":
                return
            
            if self.parent_window and hasattr(self.parent_window, 'update_status'):
                self.parent_window.update_status(message, is_warning)
            elif self.status_label:
                self.status_label.setText(message)
                if is_warning:
                    self.status_label.setStyleSheet("color: #f39c12;")
                else:
                    self.status_label.setStyleSheet("")
        except Exception as e:
            print(f"Error updating status: {e}")
    
    def dropEvent(self, event):
        try:
            if event.mimeData().hasText():
                text_data = event.mimeData().text()
                
                try:
                    data = json.loads(text_data)
                    node_type = data["type"]
                    name = data["name"]
                    color = data["color"]
                except json.JSONDecodeError:
                    node_type = text_data
                    names = {
                        "startofwork": ("Start of Work", "#2ecc71"),
                        "openurl": ("Open URL", "#3498db"),
                        "click": ("Click", "#e67e22"),
                        "type": ("Type", "#9b59b6"),
                        "parsedata": ("Parse Data", "#1abc9c"),
                        "screenshot": ("Screenshot", "#f39c12"),
                        "convertexcel": ("Convert Excel", "#95a5a6"),
                        "forloop": ("For Loop", "#e74c3c"),
                        "if": ("If", "#e74c3c"),
                        "end": ("End", "#7f8c8d"),
                        "reload": ("Reload", "#f39c12"),
                        "sendtelegram": ("Send TG", "#0088cc"),
                        "savedata": ("Save Data", "#27ae60"),
                        "endsession": ("End Session", "#c0392b")
                    }
                    name, color = names.get(node_type, (node_type, "#3498db"))
                
                pos = self.mapToScene(event.position().toPoint())
                self.add_block_with_animation(node_type, name, pos.x() - 80, pos.y() - 30, color)
                event.acceptProposedAction()
            else:
                event.ignore()
        except Exception as e:
            print(f"Error in dropEvent: {e}")
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def mousePressEvent(self, event):
        item = self.itemAt(event.pos())
        is_block = isinstance(item, GraphNode) or (item and item.parentItem() and isinstance(item.parentItem(), GraphNode))
        is_port = isinstance(item, PortItem)
        
        if event.button() == Qt.MouseButton.LeftButton:
            if is_block or is_port:
                self._dragging_block = True
                self._is_panning = False
                super().mousePressEvent(event)
            else:
                self._dragging_block = False
                self._is_panning = True
                self._last_pan_pos = event.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
                self.setDragMode(QGraphicsView.DragMode.NoDrag)
                event.accept()
            return
        elif event.button() == Qt.MouseButton.MiddleButton:
            self._dragging_block = False
            self._is_panning = True
            self._last_pan_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
            event.accept()
            return
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        self._mouse_scene_pos = self.mapToScene(event.pos())
        
        if self._is_panning and self._last_pan_pos is not None:
            delta = event.pos() - self._last_pan_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self._last_pan_pos = event.pos()
            event.accept()
            return
        
        # ПРИНУДИТЕЛЬНО обновляем ВСЕ соединения при движении любого блока
        for node in self.nodes.values():
            if node._is_dragging:
                for edge_id, edge in list(self.edges.items()):
                    try:
                        if edge.scene():
                            edge._cached_path = None
                            edge._cached_obstacles_hash = None
                            edge._cached_start = None
                            edge._cached_end = None
                            edge.update_position()
                    except RuntimeError:
                        pass
                break
        
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_panning:
                self._is_panning = False
                self._last_pan_pos = None
                self.setCursor(Qt.CursorShape.ArrowCursor)
                self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
                event.accept()
                return
            elif self._dragging_block:
                self._dragging_block = False
        elif event.button() == Qt.MouseButton.MiddleButton:
            if self._is_panning:
                self._is_panning = False
                self._last_pan_pos = None
                self.setCursor(Qt.CursorShape.ArrowCursor)
                self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
                event.accept()
                return
        super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event):
        old_pos = self.mapToScene(event.position().toPoint())
        delta = event.angleDelta().y()
        if delta > 0:
            if self.zoom_factor < self.zoom_max:
                scale_factor = self.zoom_step
                self.zoom_factor *= self.zoom_step
            else:
                scale_factor = 1.0
        else:
            if self.zoom_factor > self.zoom_min:
                scale_factor = 1 / self.zoom_step
                self.zoom_factor /= self.zoom_step
            else:
                scale_factor = 1.0
        self.scale(scale_factor, scale_factor)
        new_pos = self.mapToScene(event.position().toPoint())
        delta = new_pos - old_pos
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + int(delta.x()))
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() + int(delta.y()))
        event.accept()