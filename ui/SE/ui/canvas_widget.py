# ui/SE/ui/canvas_widget.py - ПОЛНАЯ ВЕРСИЯ

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


class LightningEffectItem(QGraphicsItem):
    """Анимация молнии для появления блока"""
    
    def __init__(self, pos, color="#ff9900", parent=None):
        super().__init__(parent)
        self.setPos(pos)
        self._opacity = 0.0
        self._progress = 0.0
        self._finished = False
        self._color = QColor(color)
        
        self.anim = QVariantAnimation()
        self.anim.setDuration(600)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.valueChanged.connect(self.update_animation)
        self.anim.finished.connect(self.finish)
        self.anim.start()
        
        self.setZValue(100)
    
    def update_animation(self, value):
        self._progress = value
        self._opacity = 1.0 if value < 0.25 else max(0, 1.0 - (value - 0.25) / 0.35)
        self.update()
    
    def finish(self):
        self._finished = True
        self.hide()
        QTimer.singleShot(100, self.deleteLater)
    
    def boundingRect(self):
        return QRectF(-150, -150, 300, 300)
    
    def paint(self, painter, option, widget):
        if self._finished or self._opacity < 0.01:
            return
        
        painter.setOpacity(self._opacity)
        
        center = QPointF(0, 0)
        radius = 120 * (0.3 + 0.7 * self._progress)
        
        # Внешнее свечение
        gradient = QRadialGradient(center, radius * 2)
        gradient.setColorAt(0, QColor(255, 255, 255, 200))
        gradient.setColorAt(0.1, QColor(200, 230, 255, 150))
        gradient.setColorAt(0.3, QColor(self._color).lighter(150))
        gradient.setColorAt(0.6, QColor(self._color))
        gradient.setColorAt(1, QColor(self._color).darker(200))
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(center, radius * 2, radius * 2)
        
        # Яркое ядро
        core_radius = 50 * (0.3 + 0.7 * self._progress)
        core_gradient = QRadialGradient(center, core_radius)
        core_gradient.setColorAt(0, QColor(255, 255, 255, 255))
        core_gradient.setColorAt(0.5, QColor(255, 255, 200, 200))
        core_gradient.setColorAt(1, QColor(255, 200, 100, 100))
        
        painter.setBrush(QBrush(core_gradient))
        painter.drawEllipse(center, core_radius, core_radius)
        
        # Лучи молнии
        painter.setPen(QPen(QColor(255, 255, 255, int(150 * self._opacity)), 2))
        for i in range(12):
            angle = i * math.pi / 6 + self._progress * 3
            length = 80 + 50 * math.sin(self._progress * 25 + i * 1.5)
            x1 = center.x() + 40 * math.cos(angle)
            y1 = center.y() + 40 * math.sin(angle)
            x2 = center.x() + (40 + length) * math.cos(angle + 0.3 * math.sin(self._progress * 12 + i))
            y2 = center.y() + (40 + length) * math.sin(angle + 0.3 * math.sin(self._progress * 12 + i))
            
            points = [
                QPointF(x1, y1),
                QPointF((x1 + x2) / 2 + 25 * math.sin(angle + 1.5), (y1 + y2) / 2 + 25 * math.cos(angle + 1.5)),
                QPointF((x1 + x2) / 2 + 35 * math.sin(angle + 2.5), (y1 + y2) / 2 + 35 * math.cos(angle + 2.5)),
                QPointF(x2, y2)
            ]
            painter.drawPolyline(QPolygonF(points))
        
        # Кольца расширения
        for i in range(4):
            ring_radius = 50 + 80 * self._progress + i * 20
            ring_alpha = int(100 * (1.0 - self._progress / 0.6) * self._opacity)
            if ring_alpha > 0:
                painter.setPen(QPen(QColor(200, 220, 255, ring_alpha), 2))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(center, ring_radius, ring_radius)
        
        painter.setOpacity(1.0)


class PortItem(QGraphicsEllipseItem):
    """Порт для соединений"""
    
    def __init__(self, port_type, parent_node, size=8):
        super().__init__(-size/2, -size/2, size, size, parent_node)
        self.port_type = port_type
        self.parent_node = parent_node
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        
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


class GraphEdge(QGraphicsPathItem):
    """Графическое представление соединения"""
    
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
    
    def set_source(self, node):
        self.source = node
        self.update_position()
    
    def set_destination(self, node):
        self.destination = node
        self.update_position()
    
    def update_position(self):
        if self.source and self.destination:
            self.prepareGeometryChange()
            source_point = self.source.get_port_position(self.source_port)
            dest_point = self.destination.get_port_position(self.dest_port)
            self.source_pos = source_point
            self.dest_pos = dest_point
            self.setPos(QPointF(0, 0))
            self.update_path()

    def update_path(self):
        if not hasattr(self, 'source_pos') or not hasattr(self, 'dest_pos'):
            return
        source_port_pos = self.source_pos
        dest_port_pos = self.dest_pos
        target_pos = QPointF(dest_port_pos.x() - 15, dest_port_pos.y())
        path = QPainterPath()
        path.moveTo(source_port_pos)
        dx = target_pos.x() - source_port_pos.x()
        ctrl1 = QPointF(source_port_pos.x() + dx * 0.25, source_port_pos.y())
        ctrl2 = QPointF(target_pos.x() - dx * 0.25, target_pos.y())
        path.cubicTo(ctrl1, ctrl2, target_pos)
        self.setPath(path)
        self.arrow_center = QPointF(dest_port_pos.x() - 15, dest_port_pos.y())
    
    def paint(self, painter, option, widget=None):
        if not self.source or not self.destination:
            return
        
        color = self.data_color
        pen = QPen(color)
        pen.setWidth(self.pen_width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawPath(self.path())
        
        # Стрелка
        arrow_center = self.arrow_center
        arrow_size = 10
        arrow_width = 6
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color, 1))
        points = [
            arrow_center + QPointF(arrow_size/2, 0),
            arrow_center + QPointF(-arrow_size/2, -arrow_width/2),
            arrow_center + QPointF(-arrow_size/2, arrow_width/2)
        ]
        painter.drawPolygon(QPolygonF(points))


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
        
        # Стиль карточки
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
            return port.scenePos() + QPointF(port.rect().width() / 2, port.rect().height() / 2)
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
        self.is_dragging_connection = True
        self.drag_start_port = port_name
        
        if port_name in self.ports:
            self.ports[port_name].set_highlighted(True)
        
        self.temp_connection_line = QGraphicsLineItem()
        pen = QPen(QColor("#ffffff"), 2, Qt.PenStyle.DashLine)
        pen.setDashPattern([5, 5])
        self.temp_connection_line.setPen(pen)
        self.temp_connection_line.setZValue(1000)
        self.scene().addItem(self.temp_connection_line)
        
        start_pos = self.get_port_position(port_name)
        self.temp_connection_line.setLine(start_pos.x(), start_pos.y(), start_pos.x(), start_pos.y())
    
    def update_temp_connection(self, pos):
        if self.temp_connection_line and self.drag_start_port:
            start_pos = self.get_port_position(self.drag_start_port)
            self.temp_connection_line.setLine(start_pos.x(), start_pos.y(), pos.x(), pos.y())
    
    def finish_connection_drag(self, target_node, target_port):
        if not self.drag_start_port:
            return
        
        if self.drag_start_port == "output" and target_port == "input":
            from_node, to_node = self, target_node
            from_port, to_port = "output", "input"
        elif self.drag_start_port == "input" and target_port == "output":
            from_node, to_node = target_node, self
            from_port, to_port = "output", "input"
        elif self.block.node_type == "if" and self.drag_start_port in ["true", "false"] and target_port == "input":
            from_node, to_node = self, target_node
            from_port, to_port = self.drag_start_port, "input"
        else:
            self.cancel_connection_drag()
            return
        
        if from_node == to_node:
            self.cancel_connection_drag()
            return
        
        for edge in from_node.edges:
            if edge.destination == to_node:
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
        
        self.canvas.add_connection(connection, "data")
        self.cancel_connection_drag()
    
    def cancel_connection_drag(self):
        self.is_dragging_connection = False
        self.drag_start_port = None
        if self.temp_connection_line:
            self.scene().removeItem(self.temp_connection_line)
            self.temp_connection_line = None
        
        for port in self.ports.values():
            port.set_highlighted(False)
    
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
        
        title_action = menu.addAction(f"Block: {self.block.name}")
        title_action.setEnabled(False)
        menu.addSeparator()
        
        rename_action = menu.addAction("✏️ Rename")
        rename_action.triggered.connect(self._rename_block)
        
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(self._delete_block)
        
        menu.addAction(rename_action)
        menu.addAction(delete_action)
        
        if self.parent_node:
            menu.addSeparator()
            exit_action = menu.addAction(f"📤 Exit from '{self.parent_node.block.name}'")
            exit_action.triggered.connect(self.remove_from_parent)
            menu.addAction(exit_action)
        
        menu.exec(event.screenPos())
    
    def _rename_block(self):
        new_name, ok = QInputDialog.getText(None, "Rename Block", "Enter new name:", text=self.block.name)
        if ok and new_name:
            self.block.name = new_name
            self.text_item.setPlainText(new_name)
            self._center_text()
            if hasattr(self.canvas.parent_window, 'auto_save_project'):
                self.canvas.parent_window.auto_save_project()
    
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
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            for port_name, port in self.ports.items():
                port_pos = port.mapFromParent(pos)
                if port.contains(port_pos):
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
            scene_pos = self.mapToScene(event.pos())
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
                scene_pos = self.mapToScene(event.pos())
                items = self.scene().items(scene_pos)
                target_port = None
                target_node = None
                for item in items:
                    if isinstance(item, PortItem):
                        target_port = item
                        target_node = item.parent_node
                        break
                    elif isinstance(item, GraphNode):
                        target_node = item
                        if self.drag_start_port == "output" and "input" in target_node.ports:
                            target_port = target_node.ports["input"]
                        elif self.drag_start_port == "input" and "output" in target_node.ports:
                            target_port = target_node.ports["output"]
                        elif self.drag_start_port in ["true", "false"] and "input" in target_node.ports:
                            target_port = target_node.ports["input"]
                        break
                if target_port and target_node and target_node != self:
                    self.finish_connection_drag(target_node, target_port.port_type)
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
    
    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            if self._is_dragging:
                new_pos = value
                self.block.position["x"] = new_pos.x()
                self.block.position["y"] = new_pos.y()
                for edge in self.edges:
                    edge.update_position()
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
        self.edges: Dict[str, GraphEdge] = {}
        self.next_id = 1
        
        # Сетка с точками
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
        self.grid_update_timer.timeout.connect(self.update_grid)
        self.grid_update_timer.start(16)
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_nest_states)
        self.update_timer.start(50)
        
        self.status_label = None
    
    # ========================================================================
    # МЕТОДЫ ДЛЯ СЕТКИ
    # ========================================================================
    
    def _get_key(self, x, y):
        return f"{int(x)}_{int(y)}"
    
    def _update_visible_points(self, rect):
        padding = 200
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
    
    def update_grid(self):
        if self._mouse_scene_pos:
            self.viewport().update()
    
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        
        if not self.grid_enabled:
            return
        
        if not self._mouse_scene_pos:
            self._mouse_scene_pos = QPointF(0, 0)
        
        self._update_visible_points(rect)
        
        if not self._grid_points:
            return
        
        spacing = self.grid_spacing / self.zoom_factor
        spacing = max(10, min(100, spacing))
        
        dot_size = self.grid_dot_radius / self.zoom_factor
        dot_size = max(1, min(8, dot_size))
        
        mouse_x = self._mouse_scene_pos.x()
        mouse_y = self._mouse_scene_pos.y()
        
        repel_radius = self.repel_radius / self.zoom_factor
        repel_radius = max(50, min(500, repel_radius))
        
        for key, point in self._grid_points.items():
            px, py = point[0], point[1]
            
            if not rect.contains(px, py):
                continue
            
            dx = px - mouse_x
            dy = py - mouse_y
            dist = math.sqrt(dx*dx + dy*dy)
            
            velocity = self._grid_velocities.get(key, [0.0, 0.0])
            vx, vy = velocity[0], velocity[1]
            
            if dist < repel_radius and dist > 1:
                angle = math.atan2(dy, dx)
                force = 3.0 * (1 - dist / repel_radius) ** 3
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
                vx += norm_x * 0.25
                vy += norm_y * 0.25
            
            vx *= 0.85
            vy *= 0.85
            
            new_x = px + vx
            new_y = py + vy
            
            speed = math.sqrt(vx*vx + vy*vy)
            if speed < 0.05 and return_dist < 1.0:
                vx = 0
                vy = 0
                new_x = orig_x
                new_y = orig_y
            
            self._grid_velocities[key] = [vx, vy]
            self._grid_points[key] = [new_x, new_y]
            
            if dist < repel_radius:
                t = 1.0 - (dist / repel_radius)
                brightness = 150 + int(105 * t)
                alpha = 200 + int(55 * t)
                color = QColor(160, 216, 255, alpha)
                current_dot_size = dot_size * (1.0 + 0.5 * t)
            else:
                color = QColor(100, 180, 255, 80)
                current_dot_size = dot_size
            
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(new_x, new_y), current_dot_size, current_dot_size)
            
            if dist < repel_radius * 0.5:
                center_size = current_dot_size * 0.4
                painter.setBrush(QBrush(QColor(255, 255, 255, 150)))
                painter.drawEllipse(QPointF(new_x, new_y), center_size, center_size)
    
    # ========================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С БЛОКАМИ
    # ========================================================================
    
    def add_block_with_animation(self, node_type: str, name: str, x: float, y: float, color: str = "#3498db"):
        """Добавляет блок с анимацией молнии"""
        print(f"⚡ [CANVAS] add_block_with_animation: {name} at ({x}, {y})")
        
        node = self.add_block_from_data(node_type, name, x, y, color)
        
        if not node:
            print(f"❌ [CANVAS] Failed to create block: {name}")
            return None
        
        print(f"✅ [CANVAS] Block created and added: id={node.block.id}")
        
        node.setOpacity(0.0)
        node.setScale(0.3)
        
        effect = LightningEffectItem(QPointF(x + 80, y + 30), color)
        self.scene.addItem(effect)
        print(f"⚡ [CANVAS] Lightning effect added")
        
        self.scene.update()
        self.viewport().update()
        
        anim = QVariantAnimation()
        anim.setDuration(600)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        
        def update_anim(value):
            ease = 1 - math.pow(1 - value, 3)
            node.setOpacity(ease)
            node.setScale(0.3 + 0.7 * ease)
            node.setPos(x, y - 15 * (1 - ease))
            self.viewport().update()
        
        def finish_anim():
            node.setPos(x, y)
            node.setScale(1.0)
            node.setOpacity(1.0)
            self.scene.update()
            self.viewport().update()
            print(f"✅ [CANVAS] Block '{name}' fully appeared!")
            self._update_status(f"⚡ Block '{name}' appeared!")
        
        anim.valueChanged.connect(update_anim)
        anim.finished.connect(finish_anim)
        anim.start()
        
        return node
    
    def add_block_from_data(self, node_type: str, name: str, x: float = 0, y: float = 0, color: str = "#3498db"):
        """Создает блок и добавляет его на сцену"""
        from ui.SE.core.models import Block
        
        try:
            print(f"🟣 [CANVAS] add_block_from_data: type={node_type}, name={name}, pos=({x},{y})")
            
            block = Block(
                block_id=self.next_id,
                node_type=node_type,
                name=name,
                x=x,
                y=y,
                color=color
            )
            block.params = block.get_default_params()
            print(f"🟣 [CANVAS] Block created: id={block.id}")
            
            node = GraphNode(block, self)
            node.setOpacity(0.0)
            node.setScale(0.3)
            node.setPos(x, y)
            
            self.scene.addItem(node)
            self.nodes[block.id] = node
            print(f"🟣 [CANVAS] Node added to scene, total: {len(self.nodes)}")
            
            self.next_id += 1
            print(f"🟣 [CANVAS] next_id now: {self.next_id}")
            
            self.scene.clearSelection()
            node.setSelected(True)
            self.block_selected.emit(node)
            
            self.scene.update()
            self.viewport().update()
            
            print(f"✅ [CANVAS] Block '{name}' added to scene")
            
            return node
        except Exception as e:
            print(f"❌ [CANVAS] Error adding block: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def remove_block_with_animation(self, block_id: int):
        """Удаляет блок с анимацией исчезновения"""
        if block_id not in self.nodes:
            return False
        
        node = self.nodes[block_id]
        print(f"💨 [CANVAS] Removing block with animation: {node.block.name}")
        
        anim = QVariantAnimation()
        anim.setDuration(400)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        
        def update_anim(value):
            node.setOpacity(value)
            node.setScale(0.3 + 0.7 * value)
            node.setPos(node.pos().x(), node.pos().y() + 5 * (1 - value))
            self.viewport().update()
        
        def finish_anim():
            self.remove_block(block_id)
            self.scene.update()
            self.viewport().update()
            print(f"✅ [CANVAS] Block '{node.block.name}' removed")
        
        anim.valueChanged.connect(update_anim)
        anim.finished.connect(finish_anim)
        anim.start()
        
        return True
    
    def remove_block(self, block_id):
        """Удаляет блок без анимации"""
        if block_id in self.nodes:
            node = self.nodes[block_id]
            print(f"🗑️ [CANVAS] Removing block: {node.block.name}")
            
            edges_to_remove = []
            for edge_id, edge in self.edges.items():
                if edge.source == node or edge.destination == node:
                    edges_to_remove.append(edge_id)
            
            for edge_id in edges_to_remove:
                edge = self.edges[edge_id]
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
        """Удаляет все выбранные блоки с анимацией"""
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
    
    # ========================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С СОЕДИНЕНИЯМИ
    # ========================================================================
    
    def add_connection(self, connection, connection_type="data"):
        edge = GraphEdge(connection, self, connection_type)
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
        for edge in self.edges.values():
            edge.update_position()
    
    # ========================================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С ВЛОЖЕННОСТЬЮ
    # ========================================================================
    
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
    
    # ========================================================================
    # УПРАВЛЕНИЕ КАНВАСОМ
    # ========================================================================
    
    def get_all_blocks(self):
        return list(self.nodes.values())
    
    def clear(self):
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
    
    # ========================================================================
    # ОБРАБОТЧИКИ СОБЫТИЙ
    # ========================================================================
    
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
            import traceback
            traceback.print_exc()
    
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