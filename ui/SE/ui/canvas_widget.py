# ui/SE/ui/canvas_widget.py - ПОЛНАЯ ВЕРСИЯ с print маркерами

import math
import json
from typing import Dict, List, Optional, Any
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import QGraphicsItem
from ui.SE.core.models import Block, Connection


class CollapseButton(QGraphicsEllipseItem):
    """Кнопка сворачивания/разворачивания блока (+/-) внутри блока"""
    
    def __init__(self, parent_node):
        print(f"🔘 [CollapseButton] __init__ START")
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
        print(f"🔘 [CollapseButton] __init__ END")
    
    def _center_text(self):
        text_rect = self.text.boundingRect()
        self.text.setPos(-text_rect.width() / 2, -text_rect.height() / 2)
    
    def set_collapsed(self, collapsed):
        self.collapsed = collapsed
        self.text.setPlainText("+" if collapsed else "−")
        self._center_text()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"🔘 [CollapseButton] clicked on {self.parent_node.block.name}")
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


class GraphNode(QGraphicsRectItem):
    """Графическое представление блока на канвасе с портами слева/справа"""
    
    def __init__(self, block, canvas):
        print(f"🎨 [GraphNode] __init__ START: id={block.id}, name={block.name}")
        
        self.original_width = block.size["width"]
        self.original_height = block.size["height"]
        self.original_rect = QRectF(0, 0, self.original_width, self.original_height)
        
        super().__init__(self.original_rect)
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
        
        self.default_brush = QBrush(QColor(block.color))
        self.drop_target_brush = QBrush(QColor(block.color).lighter(130))
        self.ready_brush = QBrush(QColor(block.color).lighter(150))
        self.setBrush(self.default_brush)
        
        pen = QPen(QColor("#2c3e50"))
        pen.setWidth(2)
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
        print(f"✅ [GraphNode] __init__ END: pos=({block.position['x']}, {block.position['y']})")
    
    def _create_collapse_button(self):
        self.collapse_button = CollapseButton(self)
        self.collapse_button.setPos(self.rect().width() - 10, 5)
    
    def analyze_external_connections(self):
        external_conns = []
        for child in self.child_nodes:
            for edge in child.edges:
                other_node = edge.source if edge.destination == child else edge.destination
                if not self._is_descendant(other_node):
                    external_conns.append({
                        'child': child,
                        'edge': edge,
                        'other_node': other_node,
                        'direction': 'out' if edge.source == child else 'in'
                    })
        return external_conns

    def _is_descendant(self, node):
        current = node
        while current:
            if current == self:
                return True
            current = current.parent_node
        return False
    
    def _center_text(self):
        text_rect = self.text_item.boundingRect()
        if self.collapse_button:
            self.text_item.setPos(10, (self.rect().height() - text_rect.height()) / 2)
        else:
            self.text_item.setPos((self.rect().width() - text_rect.width()) / 2, (self.rect().height() - text_rect.height()) / 2)
    
    def create_ports(self):
        rect = self.rect()
        port_size = 8
        
        input_port = PortItem("input", self, port_size)
        input_port.setBrush(QBrush(QColor("#e74c3c")))
        input_port.setPen(QPen(QColor("#c0392b"), 1))
        input_port.setPos(0, rect.height() / 2)
        input_port.setZValue(2)
        input_port.setData(0, "input")
        
        output_port = PortItem("output", self, port_size)
        output_port.setBrush(QBrush(QColor("#2ecc71")))
        output_port.setPen(QPen(QColor("#27ae60"), 1))
        output_port.setPos(rect.width(), rect.height() / 2)
        output_port.setZValue(2)
        output_port.setData(0, "output")
        
        self.ports["input"] = input_port
        self.ports["output"] = output_port
        print(f"🔌 [GraphNode] Ports created for {self.block.name}")
    
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
        print(f"🚀 [GraphNode] start_connection_drag: {port_name} from {self.block.name}")
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
        self._update_status(f"Drag from {port_name.upper()} port to connect...", is_warning=True)
    
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
        print(f"🔗 [GraphNode] Connection created: {from_node.block.name} → {to_node.block.name}")
        self._update_status(f"✓ Connected {from_node.block.name} → {to_node.block.name}")
        self.cancel_connection_drag()
    
    def cancel_connection_drag(self):
        self.is_dragging_connection = False
        self.drag_start_port = None
        if self.temp_connection_line:
            self.scene().removeItem(self.temp_connection_line)
            self.temp_connection_line = None
        for port in self.ports.values():
            port.set_highlighted(False)
    
    def _animate_child_appearance(self, child_node):
        child_node.setOpacity(0.0)
        anim = QVariantAnimation()
        anim.setDuration(300)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.valueChanged.connect(lambda v, node=child_node: node.setOpacity(v))
        anim_id = id(anim)
        self._animations[anim_id] = anim
        anim.finished.connect(lambda: self._safe_remove_animation(anim_id))
        anim.start()
    
    def _animate_collapse(self, child):
        for edge in child.edges[:]:
            other_node = edge.source if edge.destination == child else edge.destination
            if not self._is_descendant(other_node):
                continue
            else:
                edge.hide()
        child.show()
        anim = QVariantAnimation()
        anim.setDuration(200)
        anim.setStartValue(1.0)
        anim.setEndValue(0.0)
        anim.valueChanged.connect(lambda v, node=child: node.setOpacity(v))
        anim.finished.connect(child.hide)
        anim_id = id(anim)
        self._animations[anim_id] = anim
        anim.finished.connect(lambda: self._safe_remove_animation(anim_id))
        anim.start()

    def _animate_expand(self, child):
        child.show()
        child.setOpacity(0.0)
        for edge in child.edges:
            edge.show()
        anim = QVariantAnimation()
        anim.setDuration(200)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.valueChanged.connect(lambda v, node=child: node.setOpacity(v))
        anim_id = id(anim)
        self._animations[anim_id] = anim
        anim.finished.connect(lambda: self._safe_remove_animation(anim_id))
        anim.start()
    
    def _start_nest_animation(self, dragged_node):
        self.nest_animation_active = True
        if hasattr(self, 'hover_animation_id') and self.hover_animation_id:
            self._safe_remove_animation(self.hover_animation_id)
            self.hover_animation_id = None
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
        self.setBrush(self.drop_target_brush)
        self.setToolTip(f"Drop to nest '{dragged_node.block.name}' inside")
        dragged_node.potential_parent = self
        dragged_node.ready_to_nest = True
    
    def _stop_nest_animation(self):
        self.nest_animation_active = False
        if hasattr(self, 'hover_animation_id') and self.hover_animation_id:
            self._safe_remove_animation(self.hover_animation_id)
            self.hover_animation_id = None
        self.setScale(1.0)
    
    def _update_hover_scale(self, value):
        self.setScale(value)
    
    def _safe_remove_animation(self, anim_id):
        if anim_id is None:
            return
        try:
            if anim_id in self._animations:
                try:
                    anim = self._animations[anim_id]
                    if anim.state() != QVariantAnimation.State.Stopped:
                        anim.stop()
                except (RuntimeError, AttributeError):
                    pass
                finally:
                    del self._animations[anim_id]
        except (RuntimeError, KeyError):
            pass
    
    def _cleanup_animations(self):
        to_remove = []
        for anim_id, anim in list(self._animations.items()):
            try:
                if anim.state() == QVariantAnimation.State.Stopped:
                    to_remove.append(anim_id)
            except (RuntimeError, AttributeError):
                to_remove.append(anim_id)
        for anim_id in to_remove:
            try:
                if anim_id in self._animations:
                    del self._animations[anim_id]
            except KeyError:
                pass
    
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
                self._update_status(f"Drop {dragged_node.block.name} into {self.block.name}")
                self.hover_check_timer.start(50)
            else:
                self._clear_nest_opportunity()
        else:
            self._clear_nest_opportunity()
    
    def hoverEnterEvent(self, event):
        super().hoverEnterEvent(event)
        dragged_blocks = self._get_dragged_blocks()
        if dragged_blocks:
            self.hoverMoveEvent(event)
    
    def hoverLeaveEvent(self, event):
        super().hoverLeaveEvent(event)
        self._clear_nest_opportunity()
        self.last_mouse_pos = None
        if not self.is_dragging_connection:
            self._update_status("")
    
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
                self.setBrush(self.ready_brush)
                self.setScale(1.05)
                time_left = max(0, 500 - self.hover_check_timer.interval())
                self._update_status(f"Hold for {time_left//100}0ms to nest...", is_warning=True)
            else:
                self._clear_nest_opportunity()
    
    def _update_status(self, message, is_warning=False):
        if self.canvas and hasattr(self.canvas, '_update_status'):
            self.canvas._update_status(message, is_warning)
    
    def contains(self, point):
        return self.rect().contains(point)
    
    def add_child(self, child_node):
        if child_node not in self.child_nodes:
            print(f"👪 [GraphNode] Adding child {child_node.block.name} to {self.block.name}")
            self.child_nodes.append(child_node)
            child_node.parent_node = self
            if child_node.block.id not in self.block.children_ids:
                self.block.children_ids.append(child_node.block.id)
            if child_node.block.parent_id != self.block.id:
                child_node.block.parent_id = self.block.id
            if not self.collapse_button and len(self.child_nodes) > 0:
                self._create_collapse_button()
                self._center_text()
            self._animate_child_appearance(child_node)
    
    def remove_child(self, child_node):
        if child_node in self.child_nodes:
            print(f"👪 [GraphNode] Removing child {child_node.block.name} from {self.block.name}")
            self.child_nodes.remove(child_node)
            child_node.parent_node = None
            if child_node.block.id in self.block.children_ids:
                self.block.children_ids.remove(child_node.block.id)
            if not self.child_nodes and self.collapse_button:
                self.scene().removeItem(self.collapse_button)
                self.collapse_button = None
                self._center_text()
    
    def remove_from_parent(self):
        if self.parent_node:
            old_parent = self.parent_node
            print(f"📤 [GraphNode] Removing {self.block.name} from parent {old_parent.block.name}")
            old_parent.remove_child(self)
            self.block.parent_id = None
            edges_to_remove = []
            for edge_id, edge in self.canvas.edges.items():
                if (edge.source == old_parent and edge.destination == self) or \
                   (edge.destination == old_parent and edge.source == self):
                    edges_to_remove.append(edge_id)
            for edge_id in edges_to_remove:
                self.canvas.scene.removeItem(self.canvas.edges[edge_id])
                del self.canvas.edges[edge_id]
            if hasattr(self.canvas.parent_window, 'update_explorer'):
                self.canvas.parent_window.update_explorer()
            if hasattr(self.canvas.parent_window, 'auto_save_project'):
                self.canvas.parent_window.auto_save_project()
            self._update_status(f"✓ {self.block.name} removed from parent")
    
    def toggle_collapse(self):
        self.collapsed = not self.collapsed
        if self.collapse_button:
            self.collapse_button.set_collapsed(self.collapsed)
        if self.collapsed:
            external = self.analyze_external_connections()
            for conn_info in external:
                self._create_proxy_edge(conn_info)
            for child in self.child_nodes:
                self._animate_collapse(child)
        else:
            for proxy in self.proxy_edges:
                if proxy in self.canvas.edges.values():
                    self.canvas.scene.removeItem(proxy)
                    for edge_id, edge in list(self.canvas.edges.items()):
                        if edge == proxy:
                            del self.canvas.edges[edge_id]
                            break
            self.proxy_edges.clear()
            for child in self.child_nodes:
                self._animate_expand(child)
            for child in self.child_nodes:
                for edge in child.edges:
                    edge.show()
        self.canvas.update_connections()
        self.update()

    def _create_proxy_edge(self, conn_info):
        from ui.SE.core.models import Connection
        child = conn_info['child']
        original_edge = conn_info['edge']
        other_node = conn_info['other_node']
        direction = conn_info['direction']
        if direction == 'out':
            proxy_conn = Connection(
                from_block_id=self.block.id,
                from_port=original_edge.source_port,
                to_block_id=other_node.block.id,
                to_port=original_edge.dest_port,
                data_type="proxy"
            )
            proxy_edge = self.canvas.add_connection(proxy_conn, "proxy")
        else:
            proxy_conn = Connection(
                from_block_id=other_node.block.id,
                from_port=original_edge.source_port,
                to_block_id=self.block.id,
                to_port=original_edge.dest_port,
                data_type="proxy"
            )
            proxy_edge = self.canvas.add_connection(proxy_conn, "proxy")
        if proxy_edge:
            proxy_edge.original_edge = original_edge
            proxy_edge.source_child = child
            self.proxy_edges.append(proxy_edge)
            original_edge.hide()
        return proxy_edge
    
    def contextMenuEvent(self, event):
        menu = QMenu()
        title_action = menu.addAction(f"Block: {self.block.name}")
        title_action.setEnabled(False)
        menu.addSeparator()
        if self.parent_node:
            parent_action = menu.addAction(f"📤 Exit from '{self.parent_node.block.name}'")
            parent_action.triggered.connect(self.remove_from_parent)
        else:
            menu.addAction("🔝 Root block (no parent)").setEnabled(False)
        if self.child_nodes:
            menu.addSeparator()
            children_menu = menu.addMenu("📋 Children")
            for child in self.child_nodes:
                child_action = children_menu.addAction(f"• {child.block.name}")
                child_action.triggered.connect(lambda checked, c=child: self.canvas.select_block(c.block.id))
        menu.addSeparator()
        if self.collapsed:
            expand_action = menu.addAction("🔽 Expand")
            expand_action.triggered.connect(lambda: self.toggle_collapse() if self.collapsed else None)
        else:
            collapse_action = menu.addAction("🔼 Collapse")
            collapse_action.triggered.connect(lambda: self.toggle_collapse() if not self.collapsed else None)
        rename_action = menu.addAction("✏️ Rename")
        rename_action.triggered.connect(self._rename_block)
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(self._delete_block)
        menu.addSeparator()
        info_action = menu.addAction(f"ID: {self.block.id}")
        info_action.setEnabled(False)
        menu.exec(event.screenPos())
    
    def _select_child(self, child_node):
        self.canvas.select_block(child_node.block.id)
    
    def _rename_block(self):
        new_name, ok = QInputDialog.getText(None, "Rename Block", "Enter new name:", text=self.block.name)
        if ok and new_name:
            old_name = self.block.name
            self.block.name = new_name
            self.text_item.setPlainText(new_name)
            self._center_text()
            print(f"✏️ [GraphNode] Block renamed: {old_name} → {new_name}")
            self._update_status(f"Renamed to '{new_name}'")
            if self.canvas and self.canvas.parent_window and hasattr(self.canvas.parent_window, 'palette'):
                self.canvas.parent_window.palette.update_reference_block(self.block.id, new_name)
            if hasattr(self.canvas.parent_window, 'auto_save_project'):
                self.canvas.parent_window.auto_save_project()
    
    def _delete_block(self):
        reply = QMessageBox.question(None, "Delete Block", f"Are you sure you want to delete '{self.block.name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            print(f"🗑️ [GraphNode] Deleting block {self.block.name} (id={self.block.id})")
            self.canvas.remove_block(self.block.id)
            self._update_status(f"Deleted '{self.block.name}'")
            if hasattr(self.canvas.parent_window, 'auto_save_project'):
                self.canvas.parent_window.auto_save_project()
    
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
                time_elapsed = self._drag_start_time.msecsTo(QTime.currentTime())
                if move_distance > QApplication.startDragDistance() or time_elapsed > 200:
                    self._is_dragging = True
                    print(f"🖱️ [GraphNode] Started dragging block {self.block.name}")
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
                        break
                if target_port and target_node and target_node != self:
                    self.finish_connection_drag(target_node, target_port.port_type)
                else:
                    self.cancel_connection_drag()
                    self._update_status("❌ Connection cancelled", is_warning=True)
                event.accept()
                return
            if self._is_dragging:
                new_pos = self.pos()
                if self._original_pos and self._original_pos != new_pos:
                    print(f"📍 [GraphNode] Block {self.block.name} moved: ({self._original_pos.x()}, {self._original_pos.y()}) → ({new_pos.x()}, {new_pos.y()})")
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
                            print(f"🏠 [GraphNode] Nesting {self.block.name} into {item.block.name}")
                            self.canvas.nest_block(self, item)
                            self._update_status(f"✓ Nested '{self.block.name}' in '{item.block.name}'")
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
            new_pos = value
            if self._is_dragging:
                old_pos = self.pos()
                delta_x = new_pos.x() - old_pos.x()
                delta_y = new_pos.y() - old_pos.y()
                self.block.position["x"] = new_pos.x()
                self.block.position["y"] = new_pos.y()
                for edge in self.edges:
                    edge.update_position()
                if self.child_nodes and (abs(delta_x) > 0 or abs(delta_y) > 0):
                    self.move_children(delta_x, delta_y)
                if hasattr(self.canvas, 'parent_window'):
                    main_window = self.canvas.parent_window
                    if hasattr(main_window, 'update_position_label'):
                        main_window.update_position_label(new_pos.x(), new_pos.y())
                return new_pos
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            if value and self.scene():
                if hasattr(self.canvas, 'parent_window'):
                    main_window = self.canvas.parent_window
                    if hasattr(main_window, 'property_editor'):
                        main_window.property_editor.set_element(self.block)
        return super().itemChange(change, value)
    
    def paint(self, painter, option, widget=None):
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        path = QPainterPath()
        path.addRoundedRect(self.rect(), self._radius, self._radius)
        painter.drawPath(path)
        if hasattr(self.block, 'is_reference_block') and self.block.is_reference_block():
            painter.setPen(QPen(QColor("#f39c12"), 2))
            painter.setFont(QFont("Arial", 12))
            painter.drawText(self.rect().adjusted(5, 5, -5, -5), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight, "🔗")
        if self.child_nodes:
            count_text = str(len(self.child_nodes))
            painter.setPen(QPen(QColor("#888888"), 1))
            painter.setFont(QFont("Arial", 8))
            painter.drawText(self.rect().adjusted(5, 5, -5, -5), Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignRight, count_text)
        if self.isSelected():
            painter.setPen(QPen(QColor("#f39c12"), 3))
            painter.drawRoundedRect(self.rect().adjusted(-2, -2, 2, 2), self._radius + 2, self._radius + 2)
        if self.is_potential_parent:
            painter.setPen(QPen(QColor("#2ecc71"), 3, Qt.PenStyle.DashLine))
            painter.drawRoundedRect(self.rect().adjusted(-5, -5, 5, 5), self._radius + 5, self._radius + 5)
            painter.setPen(QPen(QColor("#2ecc71")))
            painter.setFont(QFont("Arial", 8))
            painter.drawText(self.rect().adjusted(0, -20, 0, 0), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "▼ Drop to nest here ▼")
        if self.ready_to_nest:
            painter.setPen(QPen(QColor("#f39c12"), 3, Qt.PenStyle.DotLine))
            painter.drawRoundedRect(self.rect().adjusted(-3, -3, 3, 3), self._radius + 3, self._radius + 3)
        if self.parent_node:
            painter.setPen(QPen(QColor("#888888")))
            painter.setFont(QFont("Arial", 10))
            painter.drawText(self.rect().adjusted(5, 5, -5, -5), Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, "🏠")
    
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
        except Exception as e:
            print(f"⚠️ Auto-save error: {e}")


class PortItem(QGraphicsEllipseItem):
    """Порт для соединений (INPUT слева, OUTPUT справа)"""
    
    def __init__(self, port_type, parent_node, size=8):
        print(f"🔌 [PortItem] __init__: {port_type} for {parent_node.block.name}")
        super().__init__(-size/2, -size/2, size, size, parent_node)
        self.port_type = port_type
        self.parent_node = parent_node
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        
        self.default_brush = QBrush(QColor("#e74c3c" if port_type == "input" else "#2ecc71"))
        self.highlight_brush = QBrush(QColor("#f1c40f" if port_type == "input" else "#f39c12"))
        self.setBrush(self.default_brush)
        self.setZValue(10)
        self.setData(0, port_type)
    
    def set_highlighted(self, highlighted):
        self.setBrush(self.highlight_brush if highlighted else self.default_brush)
    
    def hoverEnterEvent(self, event):
        self.setBrush(self.highlight_brush)
        self.setScale(1.2)
        tooltip = "INPUT (receives data)" if self.port_type == "input" else "OUTPUT (sends data)"
        self.setToolTip(tooltip)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.setBrush(self.default_brush)
        self.setScale(1.0)
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            print(f"🔌 [PortItem] mousePress: {self.port_type} on {self.parent_node.block.name}")
            self.setSelected(True)
            self.parent_node.start_connection_drag(self.port_type)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.parent_node and self.parent_node.is_dragging_connection:
            scene_pos = self.mapToScene(event.pos())
            self.parent_node.update_temp_connection(scene_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.parent_node and self.parent_node.is_dragging_connection:
                scene_pos = self.mapToScene(event.pos())
                items = self.scene().items(scene_pos)
                target_port = None
                target_node = None
                for item in items:
                    if isinstance(item, PortItem) and item != self:
                        target_port = item
                        target_node = item.parent_node
                        break
                if target_port and target_node:
                    self.parent_node.finish_connection_drag(target_node, target_port.port_type)
                else:
                    self.parent_node.cancel_connection_drag()
                event.accept()
        else:
            super().mouseReleaseEvent(event)


class GraphEdge(QGraphicsPathItem):
    """Графическое представление соединения между блоками"""
    
    def __init__(self, connection, canvas, edge_type="data"):
        print(f"🔗 [GraphEdge] __init__: {connection.id} type={edge_type}")
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
        self.data_color = QColor("#3498db")
        self.inheritance_color = QColor("#9b59b6")
        self.proxy_color = QColor("#f39c12")
    
    def contextMenuEvent(self, event):
        menu = QMenu()
        delete_action = QAction("🗑️ Delete connection", menu)
        delete_action.triggered.connect(self.delete_connection)
        menu.addAction(delete_action)
        menu.addSeparator()
        info_action = QAction(f"ID: {self.connection.id}", menu)
        info_action.setEnabled(False)
        menu.addAction(info_action)
        menu.exec(event.screenPos())

    def delete_connection(self):
        if self.canvas:
            self.canvas.remove_connection(self.connection.id)
    
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
        source_rect = self.source.rect()
        dest_rect = self.destination.rect()
        source_scene_pos = self.source.scenePos()
        dest_scene_pos = self.destination.scenePos()
        source_right = source_scene_pos.x() + source_rect.width()
        dest_left = dest_scene_pos.x()
        need_special = dest_left < source_right + 10
        arrow_distance = 15
        if self.dest_port == "input":
            arrow_center = QPointF(dest_port_pos.x() - arrow_distance, dest_port_pos.y())
        else:
            arrow_center = QPointF(dest_port_pos.x() + arrow_distance, dest_port_pos.y())
        target_pos = arrow_center + QPointF(-10, 0)
        path = QPainterPath()
        path.moveTo(source_port_pos)
        if self.edge_type == "inheritance":
            dx = target_pos.x() - source_port_pos.x()
            ctrl1 = QPointF(source_port_pos.x() + dx * 0.25, source_port_pos.y())
            ctrl2 = QPointF(target_pos.x() - dx * 0.25, target_pos.y())
            path.cubicTo(ctrl1, ctrl2, target_pos)
        elif need_special and self.edge_type == "data":
            source_center_y = source_scene_pos.y() + source_rect.height() / 2
            dest_center_y = dest_scene_pos.y() + dest_rect.height() / 2
            is_above = dest_center_y < source_center_y
            vertical_offset = 30
            if is_above:
                exit_point = QPointF(source_port_pos.x(), source_scene_pos.y() - vertical_offset)
                entry_point = QPointF(target_pos.x(), dest_scene_pos.y() + dest_rect.height() + vertical_offset)
            else:
                exit_point = QPointF(source_port_pos.x(), source_scene_pos.y() + source_rect.height() + vertical_offset)
                entry_point = QPointF(target_pos.x(), dest_scene_pos.y() - vertical_offset)
            path.lineTo(exit_point)
            dx = entry_point.x() - exit_point.x()
            ctrl1 = QPointF(exit_point.x() + dx * 0.25, exit_point.y())
            ctrl2 = QPointF(entry_point.x() - dx * 0.25, entry_point.y())
            path.cubicTo(ctrl1, ctrl2, entry_point)
            path.lineTo(target_pos)
        else:
            dx = target_pos.x() - source_port_pos.x()
            ctrl1 = QPointF(source_port_pos.x() + dx * 0.25, source_port_pos.y())
            ctrl2 = QPointF(target_pos.x() - dx * 0.25, target_pos.y())
            path.cubicTo(ctrl1, ctrl2, target_pos)
        self.setPath(path)
        self.arrow_center = arrow_center
        self.arrow_base = target_pos
    
    def paint(self, painter, option, widget=None):
        if not self.source or not self.destination:
            return
        if self.edge_type == "inheritance":
            color = self.inheritance_color
            pen = QPen(color)
            pen.setWidth(self.pen_width)
            pen.setStyle(Qt.PenStyle.SolidLine)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawPath(self.path())
        elif self.edge_type == "proxy":
            color = self.proxy_color
            pen = QPen(color)
            pen.setWidth(self.pen_width)
            pen.setStyle(Qt.PenStyle.DashLine)
            pen.setDashPattern([5, 3])
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawPath(self.path())
            if self.source_child:
                painter.save()
                painter.setPen(QPen(color, 1))
                painter.setFont(QFont("Arial", 6))
                mid_point = self.path().pointAtPercent(0.5)
                painter.drawText(mid_point + QPointF(5, -5), f"↪ {self.source_child.block.name}")
                painter.restore()
        else:
            color = self.data_color
            pen = QPen(color)
            pen.setWidth(self.pen_width)
            pen.setStyle(Qt.PenStyle.SolidLine)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawPath(self.path())
            self.draw_arrow(painter, color)
        if self.isSelected():
            highlight_pen = QPen(QColor("#f39c12"), self.pen_width + 2, Qt.PenStyle.DotLine)
            painter.setPen(highlight_pen)
            painter.drawPath(self.path())
    
    def draw_arrow(self, painter, color):
        if not hasattr(self, 'arrow_center') or not self.source or not self.destination:
            return
        arrow_center = self.arrow_center
        arrow_size = 12
        arrow_width = 8
        old_pen = painter.pen()
        old_brush = painter.brush()
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(color, 1))
        points = [
            arrow_center + QPointF(arrow_size/2, 0),
            arrow_center + QPointF(-arrow_size/2, -arrow_width/2),
            arrow_center + QPointF(-arrow_size/2, arrow_width/2)
        ]
        triangle = QPolygonF(points)
        painter.drawPolygon(triangle)
        painter.setPen(old_pen)
        painter.setBrush(old_brush)
    
    def hoverEnterEvent(self, event):
        self.pen_width = 3
        self.update()
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        self.pen_width = 2
        self.update()
        super().hoverLeaveEvent(event)


class CanvasWidget(QGraphicsView):
    """Виджет канваса с поддержкой соединений"""
    
    block_selected = pyqtSignal(object)
    block_double_clicked = pyqtSignal(object)
    
    def __init__(self):
        print("🏁 [CANVAS] __init__ START")
        super().__init__()
        
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(-1000000, -1000000, 2000000, 2000000)
        self.setScene(self.scene)
        
        self.nodes: Dict[int, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        self.next_id = 1
        
        self.grid_size = 20
        self.grid_enabled = True
        self.zoom_factor = 1.0
        self.zoom_min = 0.1
        self.zoom_max = 5.0
        self.zoom_step = 1.1
        
        self.parent_window = None
        
        self._is_panning = False
        self._last_pan_pos = None
        self._dragging_block = False
        
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
        
        self.setBackgroundBrush(QBrush(QColor("#1e1e1e")))
        self.setMinimumSize(400, 300)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        self.scene.selectionChanged.connect(self.on_selection_changed)
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_nest_states)
        self.update_timer.start(50)
        
        self.status_label = None
        
        print("🏁 [CANVAS] __init__ END")
    
    def _update_status(self, message: str, is_warning: bool = False):
        try:
            if not message or message.strip() == "":
                return
            
            if self.parent_window and hasattr(self.parent_window, 'update_status'):
                self.parent_window.update_status(message, is_warning)
            elif self.parent_window and hasattr(self.parent_window, 'status_label'):
                self.parent_window.status_label.setText(message)
                if is_warning:
                    self.parent_window.status_label.setStyleSheet("color: #f39c12;")
                else:
                    self.parent_window.status_label.setStyleSheet("")
            elif self.status_label:
                self.status_label.setText(message)
                if is_warning:
                    self.status_label.setStyleSheet("color: #f39c12;")
                else:
                    self.status_label.setStyleSheet("")
        except Exception as e:
            print(f"Error updating status: {e}")
    
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
                        self._update_status(f"Drop {dragged_blocks[0].block.name} into {node.block.name}")
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
    
    def set_status_label(self, label):
        self.status_label = label
    
    def nest_block(self, child_node, parent_node):
        if child_node == parent_node:
            self._update_status("Cannot nest block in itself", is_warning=True)
            return False
        if child_node._would_create_cycle(parent_node):
            self._update_status("Cannot nest: would create cycle", is_warning=True)
            return False
        if child_node.parent_node:
            child_node.parent_node.remove_child(child_node)
        parent_node.add_child(child_node)
        child_node.setPos(parent_node.pos().x() + 50, parent_node.pos().y() + 50)
        child_node.block.parent_id = parent_node.block.id
        if child_node.block.id not in parent_node.block.children_ids:
            parent_node.block.children_ids.append(child_node.block.id)
        child_node.block.modified_at = QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
        parent_node.block.modified_at = QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate)
        self._create_inheritance_edge(parent_node, child_node)
        if hasattr(self.parent_window, 'update_explorer'):
            self.parent_window.update_explorer()
        if hasattr(self.parent_window, 'auto_save_project'):
            self.parent_window.auto_save_project()
        self._update_status(f"✓ Nested '{child_node.block.name}' in '{parent_node.block.name}'")
        return True
    
    def _create_inheritance_edge(self, parent_node, child_node):
        from ui.SE.core.models import Connection
        for edge in self.edges.values():
            if (edge.source == parent_node and edge.destination == child_node and 
                edge.edge_type == "inheritance"):
                return
        conn = Connection(
            from_block_id=parent_node.block.id,
            from_port="center",
            to_block_id=child_node.block.id,
            to_port="center",
            data_type="inheritance"
        )
        if hasattr(self.parent_window, 'project'):
            self.parent_window.project.add_connection(conn)
        self.add_connection(conn, "inheritance")
    
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
            print(f"🔗 [CANVAS] Connection added: {from_node.block.name} → {to_node.block.name}")
            return edge
        return None
    
    def update_connections(self):
        for edge in self.edges.values():
            edge.update_position()
    
    def remove_connection(self, connection_id):
        if connection_id in self.edges:
            edge = self.edges[connection_id]
            if edge.source:
                edge.source.remove_edge(edge)
            if edge.destination:
                edge.destination.remove_edge(edge)
            self.scene.removeItem(edge)
            del self.edges[connection_id]
            if self.parent_window and hasattr(self.parent_window, 'project'):
                self.parent_window.project.remove_connection(connection_id)
            print(f"🔗 [CANVAS] Connection removed: {connection_id}")
            return True
        return False
    
    def add_block_from_data(self, node_type: str, name: str, x: float = 0, y: float = 0, color: str = "#3498db"):
        """Добавляет блок из простых данных (для Drag'n'Drop)"""
        from ui.SE.core.models import Block
        
        print(f"🟣 [CANVAS] add_block_from_data - START: type={node_type}, name={name}, pos=({x},{y})")
        
        try:
            block = Block(
                block_id=self.next_id,
                node_type=node_type,
                name=name,
                x=x,
                y=y,
                color=color
            )
            print(f"🟣 [CANVAS] Block created: id={block.id}")
            
            block.params = block.get_default_params()
            print(f"🟣 [CANVAS] Default params: {block.params}")
            
            node = GraphNode(block, self)
            print(f"🟣 [CANVAS] GraphNode created")
            
            self.scene.addItem(node)
            print(f"🟣 [CANVAS] Node added to scene")
            
            self.nodes[block.id] = node
            print(f"🟣 [CANVAS] Node stored. Total blocks: {len(self.nodes)}")
            
            self.next_id += 1
            print(f"🟣 [CANVAS] next_id now: {self.next_id}")
            
            self.scene.clearSelection()
            node.setSelected(True)
            self.block_selected.emit(node)
            
            self._update_status(f"✓ Block '{name}' added to canvas")
            print(f"✅ [CANVAS] add_block_from_data - SUCCESS")
            
            return node
        except Exception as e:
            print(f"❌ [CANVAS] add_block_from_data - ERROR: {e}")
            import traceback
            traceback.print_exc()
            self._update_status(f"✗ Error creating block: {e}", is_warning=True)
            raise
    
    def get_all_blocks(self):
        return list(self.nodes.values())
    
    def add_block(self, block):
        print(f"🏗️ [CANVAS] add_block - START: id={block.id}, name={block.name}")
        
        try:
            node = GraphNode(block, self)
            self.scene.addItem(node)
            self.nodes[block.id] = node
            print(f"✅ [CANVAS] add_block - SUCCESS")
            return node
        except Exception as e:
            print(f"❌ [CANVAS] add_block - ERROR: {e}")
            raise
    
    def remove_block(self, block_id):
        print(f"🗑️ [CANVAS] remove_block - START: block_id={block_id}")
        
        if block_id in self.nodes:
            node = self.nodes[block_id]
            print(f"📦 [CANVAS] Block found: {node.block.name}")
            
            try:
                if self.parent_window and hasattr(self.parent_window, 'palette'):
                    self.parent_window.palette.remove_created_block(block_id)
                
                if node.parent_node:
                    node.parent_node.remove_child(node)
                
                for child in node.child_nodes[:]:
                    self.remove_block(child.block.id)
                
                edge_ids_to_remove = []
                for edge_id, edge in self.edges.items():
                    if edge.source == node or edge.destination == node:
                        edge_ids_to_remove.append(edge_id)
                
                for edge_id in edge_ids_to_remove:
                    self.scene.removeItem(self.edges[edge_id])
                    del self.edges[edge_id]
                
                self.scene.removeItem(node)
                del self.nodes[block_id]
                
                print(f"✅ [CANVAS] remove_block - SUCCESS")
                return True
            except Exception as e:
                print(f"❌ [CANVAS] remove_block - ERROR: {e}")
                return False
        else:
            print(f"⚠️ [CANVAS] Block not found: {block_id}")
            return False
    
    def clear(self):
        print(f"🧹 [CANVAS] clear - START. Blocks: {len(self.nodes)}, Connections: {len(self.edges)}")
        self.nodes.clear()
        self.edges.clear()
        self.scene.clear()
        self.next_id = 1
        print(f"✅ [CANVAS] clear - END")
    
    def dragEnterEvent(self, event):
        print("🔵 [CANVAS] dragEnterEvent - START")
        if event.mimeData().hasText():
            text = event.mimeData().text()
            print(f"🔵 [CANVAS] Text: {text[:100]}")
            event.acceptProposedAction()
            print("🔵 [CANVAS] Drag accepted")
        else:
            print("🔵 [CANVAS] No text, ignoring")
            event.ignore()
        print("🔵 [CANVAS] dragEnterEvent - END")
    
    def dragMoveEvent(self, event):
        print("🟢 [CANVAS] dragMoveEvent")
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        print("🔴 [CANVAS] dropEvent - START")
        print(f"🔴 [CANVAS] Drop position: {event.position()}")
        
        try:
            if event.mimeData().hasText():
                text_data = event.mimeData().text()
                print(f"🔴 [CANVAS] Text: {text_data[:100]}")
                
                try:
                    data = json.loads(text_data)
                    node_type = data["type"]
                    name = data["name"]
                    color = data["color"]
                    print(f"🔴 [CANVAS] JSON parsed: type={node_type}, name={name}")
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
                    print(f"🔴 [CANVAS] String mapped: name={name}")
                
                pos = self.mapToScene(event.position().toPoint())
                print(f"🔴 [CANVAS] Scene pos: ({pos.x()}, {pos.y()})")
                
                self.add_block_from_data(node_type, name, pos.x() - 80, pos.y() - 30, color)
                event.acceptProposedAction()
                print("🔴 [CANVAS] Drop accepted")
            else:
                print("🔴 [CANVAS] No text data")
                event.ignore()
        except Exception as e:
            print(f"🔴 [CANVAS] Error: {e}")
            import traceback
            traceback.print_exc()
        
        print("🔴 [CANVAS] dropEvent - END")
    
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
        self.update_zoom_display()
        event.accept()
    
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
            print(f"🎯 [CANVAS] Selected block: {node.block.name}")
    
    def drawBackground(self, painter, rect):
        super().drawBackground(painter, rect)
        if self.grid_enabled:
            self.draw_grid(painter, rect)
    
    def draw_grid(self, painter, rect):
        painter.setPen(QPen(QColor("#333333"), 1))
        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)
        right = int(rect.right())
        bottom = int(rect.bottom())
        step = self.grid_size
        x = left
        while x <= right:
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
            x += step
        y = top
        while y <= bottom:
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)
            y += step
        painter.setPen(QPen(QColor("#555555"), 2))
        painter.drawLine(-10, 0, 10, 0)
        painter.drawLine(0, -10, 0, 10)
    
    def update_zoom_display(self):
        if self.parent_window:
            if hasattr(self.parent_window, 'update_zoom_label'):
                self.parent_window.update_zoom_label(self.zoom_factor)