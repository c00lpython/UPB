# ui/SE/core/models.py

import uuid


class Block:
    def __init__(self, block_id: int, node_type: str, name: str, x: float, y: float, color: str):
        self.id = block_id
        self.node_type = node_type
        self.name = name
        self.position = {"x": x, "y": y}
        self.size = {"width": 160, "height": 60}
        self.color = color
        self.params = {}
        self.parent_id = None
        self.children_ids = []
    
    def get_default_params(self) -> dict:
        defaults = {
            "startofwork": {"projectName": "", "headless": True, "timeout": 30},
            "openurl": {"url": "", "waitStrategy": "load", "timeout": 30000},
        }
        return defaults.get(self.node_type, {})


class Connection:
    def __init__(self, from_block_id: int, from_port: str, to_block_id: int, to_port: str, data_type="any"):
        self.id = str(uuid.uuid4())
        self.from_block_id = from_block_id
        self.from_port = from_port
        self.to_block_id = to_block_id
        self.to_port = to_port
        self.data_type = data_type