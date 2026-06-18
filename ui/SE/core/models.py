# core/models.py
import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List


class BlockRegistry:
    """Реестр блоков на основе blocks.json"""
    
    _instance = None
    _blocks = None
    _blocks_path = Path(__file__).parent / "blocks.json"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._blocks is None:
            self._load_blocks()
    
    def _load_blocks(self):
        """Загружает блоки из blocks.json"""
        if not self._blocks_path.exists():
            raise FileNotFoundError(f"blocks.json not found at {self._blocks_path}")
        
        with open(self._blocks_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self._blocks = data.get('blocks', {})
            self._version = data.get('version', '1.0')
    
    def get_block(self, block_type: str) -> Optional[Dict[str, Any]]:
        """Возвращает описание блока по типу"""
        return self._blocks.get(block_type)
    
    def get_all_blocks(self) -> Dict[str, Dict[str, Any]]:
        """Возвращает все блоки"""
        return self._blocks.copy()
    
    def get_param_defaults(self, block_type: str) -> Dict[str, Any]:
        """Возвращает значения по умолчанию для параметров блока"""
        block = self.get_block(block_type)
        if not block:
            return {}
        return {
            key: param.get('default', '')
            for key, param in block.get('params', {}).items()
        }
    
    def get_handler(self, block_type: str) -> str:
        """Возвращает имя хендлера для блока"""
        block = self.get_block(block_type)
        if not block:
            return ''
        return block.get('handler', '')


# Для обратной совместимости с существующим кодом
class Block:
    """Класс-обёртка для блока с параметрами"""
    
    def __init__(self, block_id: int, node_type: str, name: str, x: float, y: float, color: str):
        self.id = block_id
        self.node_type = node_type
        self.name = name
        self.position = {"x": x, "y": y}
        self.size = {"width": 160, "height": 60}
        self.color = color
        self.params = self.get_default_params()
        self.parent_id = None
        self.children_ids = []
        self.created_at = None
        self.modified_at = None
    
    def get_default_params(self) -> dict:
        """Получает параметры по умолчанию из реестра"""
        registry = BlockRegistry()
        return registry.get_param_defaults(self.node_type)
    
    def to_dict(self) -> dict:
        """Конвертирует блок в словарь для JSON"""
        return {
            'id': self.id,
            'node_type': self.node_type,
            'name': self.name,
            'position': self.position,
            'size': self.size,
            'color': self.color,
            'params': self.params,
            'parent_id': self.parent_id,
            'children_ids': self.children_ids,
        }


class Connection:
    def __init__(self, from_block_id: int, from_port: str, to_block_id: int, to_port: str, data_type="any"):
        self.id = str(uuid.uuid4())
        self.from_block_id = from_block_id
        self.from_port = from_port
        self.to_block_id = to_block_id
        self.to_port = to_port
        self.data_type = data_type
        self.created_at = None


class IfBlock(Block):
    """Блок условия с двумя ветвями: true и false"""
    
    def __init__(self, block_id: int, name: str, x: float, y: float):
        super().__init__(
            block_id=block_id,
            node_type="if",
            name=name,
            x=x,
            y=y,
            color="#e74c3c"
        )
        self.true_branch_id = None
        self.false_branch_id = None
    
    def get_default_params(self) -> dict:
        """Переопределяем параметры для IfBlock"""
        return {
            "left": "",
            "operator": "eq",
            "right": "",
            "true_next": "",
            "false_next": ""
        }
    
    def set_branches(self, true_block_id: int = None, false_block_id: int = None):
        self.true_branch_id = true_block_id
        self.false_branch_id = false_block_id
        if true_block_id:
            self.params["true_next"] = str(true_block_id)
        if false_block_id:
            self.params["false_next"] = str(false_block_id)
    
    def get_branch(self, condition_result: bool) -> int:
        return self.true_branch_id if condition_result else self.false_branch_id


# Вспомогательные функции
def create_block(block_type: str, block_id: int, name: str, x: float = 0, y: float = 0) -> Block:
    """Фабрика для создания блоков"""
    registry = BlockRegistry()
    block_info = registry.get_block(block_type)
    
    if not block_info:
        raise ValueError(f"Unknown block type: {block_type}")
    
    # Цвет по умолчанию
    colors = {
        'startofwork': '#4CAF50',
        'openurl': '#2196F3',
        'click': '#FF9800',
        'type': '#9C27B0',
        'parsedata': '#00BCD4',
        'screenshot': '#607D8B',
        'convertexcel': '#795548',
        'forloop': '#3F51B5',
        'if': '#F44336',
        'reload': '#8BC34A',
        'sendtelegram': '#009688',
        'savedata': '#673AB7',
        'endsession': '#E91E63',
    }
    
    color = colors.get(block_type, '#9E9E9E')
    
    # Если тип 'if', создаём IfBlock
    if block_type == 'if':
        return IfBlock(block_id, name, x, y)
    
    return Block(block_id, block_type, name, x, y, color)