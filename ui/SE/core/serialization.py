"""
Сериализация для UPB Script Editor
Поддержка блоков, связей, вложений (parent-child)
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class UPBSerializer:
    """
    Сериализатор для UPB проектов
    Сохраняет и загружает workflow с блоками, связями и иерархией
    """
    
    VERSION = "1.0.0"
    
    def __init__(self):
        self.current_version = self.VERSION
    
    # =========================================================================
    # Сериализация блока
    # =========================================================================
    
    def serialize_block(self, node) -> Dict[str, Any]:
        """
        Сериализует GraphNode в словарь
        """
        block = node.block
        
        data = {
            "id": block.id,
            "node_type": block.node_type,
            "name": block.name,
            "position": {
                "x": block.position["x"],
                "y": block.position["y"]
            },
            "size": block.size.copy(),
            "color": block.color,
            "parent_id": block.parent_id,
            "children_ids": block.children_ids.copy(),
            "params": block.params.copy(),
            "created_at": getattr(block, 'created_at', datetime.now().isoformat()),
            "modified_at": datetime.now().isoformat()
        }
        
        return data
    
    def deserialize_block(self, data: Dict[str, Any]) -> Optional[Any]:
        """
        Десериализует блок из словаря
        """
        from ui.SE.core.models import Block
        
        block = Block(
            block_id=data["id"],
            node_type=data["node_type"],
            name=data["name"],
            x=data["position"]["x"],
            y=data["position"]["y"],
            color=data.get("color", "#3498db")
        )
        
        # Восстанавливаем параметры
        block.params = data.get("params", block.get_default_params())
        
        # Восстанавливаем размер
        if "size" in data:
            block.size = data["size"]
        
        # Восстанавливаем родительские связи
        block.parent_id = data.get("parent_id")
        block.children_ids = data.get("children_ids", [])
        
        # Восстанавливаем временные метки
        if "created_at" in data:
            block.created_at = data["created_at"]
        if "modified_at" in data:
            block.modified_at = data["modified_at"]
        
        return block
    
    # =========================================================================
    # Сериализация соединения
    # =========================================================================
    
    def serialize_connection(self, edge) -> Dict[str, Any]:
        """
        Сериализует GraphEdge в словарь
        """
        connection = edge.connection
        
        data = {
            "id": connection.id,
            "from_block_id": connection.from_block_id,
            "from_port": connection.from_port,
            "to_block_id": connection.to_block_id,
            "to_port": connection.to_port,
            "data_type": connection.data_type,
            "created_at": getattr(connection, 'created_at', datetime.now().isoformat())
        }
        
        return data
    
    def deserialize_connection(self, data: Dict[str, Any]) -> Any:
        """Десериализует соединение из словаря"""
        from ui.SE.core.models import Connection
        
        return Connection(
            from_block_id=data["from_block_id"],
            from_port=data["from_port"],
            to_block_id=data["to_block_id"],
            to_port=data["to_port"],
            data_type=data.get("data_type", "any")
        )

    # =========================================================================
    # Сохранение/загрузка проекта
    # =========================================================================
    
    def serialize_project(self, canvas) -> Dict[str, Any]:
        """
        Сериализует весь канвас в словарь
        """
        blocks_data = {}
        for block_id, node in canvas.nodes.items():
            blocks_data[str(block_id)] = self.serialize_block(node)
        
        connections_data = {}
        for conn_id, edge in canvas.edges.items():
            connections_data[conn_id] = self.serialize_connection(edge)
        
        project_name = ""
        if canvas.parent_window and hasattr(canvas.parent_window, 'project_manager'):
            pm = canvas.parent_window.project_manager
            if pm and pm.current_project:
                project_name = pm.current_project
        
        return {
            "version": self.current_version,
            "project_name": project_name,
            "created_at": datetime.now().isoformat(),
            "modified_at": datetime.now().isoformat(),
            "blocks": blocks_data,
            "connections": connections_data
        }
    
    def deserialize_project(self, data: Dict[str, Any], canvas) -> bool:
        """
        Десериализует проект из словаря в канвас
        """
        try:
            # Очищаем канвас
            canvas.clear()
            
            # Сначала создаём все блоки
            blocks_data = data.get("blocks", {})
            block_objects = {}
            
            print(f"📦 [DESERIALIZE] Найдено блоков в файле: {len(blocks_data)}")
            
            for block_id_str, block_data in blocks_data.items():
                try:
                    block = self.deserialize_block(block_data)
                    if block:
                        block_objects[block.id] = block
                        print(f"  ✅ Блок создан: id={block.id}, name={block.name}, type={block.node_type}")
                except Exception as e:
                    logger.error(f"Error deserializing block {block_id_str}: {e}")
                    print(f"  ❌ Ошибка создания блока {block_id_str}: {e}")
            
            # Добавляем блоки на канвас
            print(f"🏗️ [DESERIALIZE] Добавление блоков на канвас...")
            for block in block_objects.values():
                node = canvas.add_block_from_data(
                    block.node_type, 
                    block.name, 
                    block.position["x"], 
                    block.position["y"],
                    block.color
                )
                if node and node.block.id == block.id:
                    node.block.params = block.params
                    node.block.parent_id = block.parent_id
                    node.block.children_ids = block.children_ids
                    print(f"  ✅ Блок добавлен: {block.name} (id={block.id})")
            
            # Восстанавливаем родительские связи
            print(f"👪 [DESERIALIZE] Восстановление родительских связей...")
            for block in block_objects.values():
                if block.parent_id and block.parent_id in canvas.nodes:
                    parent_node = canvas.nodes[block.parent_id]
                    child_node = canvas.nodes.get(block.id)
                    if parent_node and child_node:
                        if child_node not in parent_node.child_nodes:
                            parent_node.add_child(child_node)
                            print(f"  ✅ Связь родитель-ребёнок: {parent_node.block.name} → {child_node.block.name}")
            
            # Восстанавливаем соединения
            connections_data = data.get("connections", {})
            print(f"🔗 [DESERIALIZE] Найдено соединений в файле: {len(connections_data)}")
            
            for conn_id, conn_data in connections_data.items():
                try:
                    from_block_id = conn_data["from_block_id"]
                    to_block_id = conn_data["to_block_id"]
                    
                    if from_block_id in canvas.nodes and to_block_id in canvas.nodes:
                        from_node = canvas.nodes[from_block_id]
                        to_node = canvas.nodes[to_block_id]
                        
                        # Создаём соединение через логику канваса
                        connection = self.deserialize_connection(conn_data)
                        
                        # Добавляем соединение на канвас
                        edge = canvas.add_connection(connection, conn_data.get("data_type", "data"))
                        
                        if edge:
                            print(f"  ✅ Соединение восстановлено: {from_node.block.name} → {to_node.block.name}")
                        else:
                            print(f"  ⚠️ Не удалось создать соединение: {from_block_id} → {to_block_id}")
                    else:
                        print(f"  ⚠️ Блоки для соединения не найдены: from={from_block_id}, to={to_block_id}")
                        
                except Exception as e:
                    logger.error(f"Error deserializing connection {conn_id}: {e}")
                    print(f"  ❌ Ошибка соединения {conn_id}: {e}")
                    import traceback
                    traceback.print_exc()
            
            logger.info(f"✅ Project deserialized: {len(blocks_data)} blocks, {len(connections_data)} connections")
            print(f"✅ [DESERIALIZE] ИТОГО: блоков={len(canvas.nodes)}, соединений={len(canvas.edges)}")
            return True
            
        except Exception as e:
            logger.error(f"Error deserializing project: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # =========================================================================
    # Работа с файлами
    # =========================================================================
    
    def save_project(self, canvas, filepath: str) -> bool:
        """
        Сохраняет канвас в файл
        """
        try:
            data = self.serialize_project(canvas)
            
            # Создаём директорию
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Project saved: {filepath}")
            print(f"💾 [SAVE] Сохранено: блоков={len(canvas.nodes)}, соединений={len(canvas.edges)}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving project: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_project(self, filepath: str, canvas) -> bool:
        """
        Загружает проект из файла в канвас
        """
        try:
            if not os.path.exists(filepath):
                logger.error(f"File not found: {filepath}")
                print(f"❌ [LOAD] Файл не найден: {filepath}")
                return False
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Проверяем версию
            version = data.get("version", "1.0.0")
            if version != self.current_version:
                logger.warning(f"Project version {version} != current {self.current_version}")
                print(f"⚠️ [LOAD] Версия проекта {version} != текущей {self.current_version}")
            
            success = self.deserialize_project(data, canvas)
            
            if success:
                logger.info(f"✅ Project loaded: {filepath}")
                logger.info(f"   Version: {version}, Blocks: {len(canvas.nodes)}")
                print(f"✅ [LOAD] Загружено: {filepath}")
                print(f"   Версия: {version}, Блоков: {len(canvas.nodes)}, Соединений: {len(canvas.edges)}")
                
                # Обновляем статус
                if hasattr(canvas, '_update_status'):
                    canvas._update_status(f"✓ Loaded project from {os.path.basename(filepath)}")
            
            return success
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            print(f"❌ [LOAD] Ошибка парсинга JSON: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading project: {e}")
            import traceback
            traceback.print_exc()
            return False


# =========================================================================
# Методы для интеграции с CanvasWidget
# =========================================================================

def add_serialization_to_canvas(canvas_class):
    """
    Добавляет методы сериализации в CanvasWidget
    """
    
    def save_to_file(self, filepath: str) -> bool:
        """Сохранить канвас в файл"""
        serializer = UPBSerializer()
        return serializer.save_project(self, filepath)
    
    def load_from_file(self, filepath: str) -> bool:
        """Загрузить канвас из файла"""
        serializer = UPBSerializer()
        return serializer.load_project(filepath, self)
    
    canvas_class.save_to_file = save_to_file
    canvas_class.load_from_file = load_from_file
    
    return canvas_class


# =========================================================================
# Глобальный экземпляр
# =========================================================================

upb_serializer = UPBSerializer()

__all__ = [
    'UPBSerializer',
    'upb_serializer',
    'add_serialization_to_canvas'
]