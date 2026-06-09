import uuid


class Block:
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
        defaults = {
            "startofwork": {
                "projectName": "", 
                "headless": True, 
                "timeout": 30
            },
            "openurl": {
                "url": "", 
                "waitStrategy": "load", 
                "timeout": 30000
            },
            "click": {
                "selector": "", 
                "selectorType": "css", 
                "clickCount": 1, 
                "waitAfter": 1000, 
                "waitForNavigation": False
            },
            "type": {
                "selector": "", 
                "selectorType": "css", 
                "text": "", 
                "clearFirst": True, 
                "pressEnter": False, 
                "delay": 0
            },
            "parsedata": {
                "varName": "", 
                "saveTo": "result", 
                "extractType": "text", 
                "attributeName": ""
            },
            "screenshot": {
                "filename": "screenshot.png", 
                "fullPage": False, 
                "selector": ""
            },
            "convertexcel": {
                "inputFile": "", 
                "outputFormat": "csv", 
                "outputFile": "", 
                "sheetName": "Sheet1"
            },
            "forloop": {
                "iterator": "item", 
                "iterableType": "variable", 
                "iterable": ""
            },
            "if": {
                "left": "", 
                "operator": "eq", 
                "right": "",
                "true_next": "",
                "false_next": ""
            },
            "end": {
                "blockType": "loop"
            },
            "reload": {
                "waitAfter": 2000, 
                "ignoreCache": True
            },
            "sendtelegram": {
                "botToken": "", 
                "chatId": "", 
                "message": "", 
                "parseMode": ""
            },
            "savedata": {
                "dataVar": "", 
                "format": "excel", 
                "outputPath": "./output", 
                "overwrite": True
            },
            "endsession": {
                "saveResults": True, 
                "closeBrowser": True, 
                "exportReport": False
            }
        }
        return defaults.get(self.node_type, {}).copy()


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
        """Устанавливает ID блоков для веток true/false"""
        self.true_branch_id = true_block_id
        self.false_branch_id = false_block_id
        if true_block_id:
            self.params["true_next"] = str(true_block_id)
        if false_block_id:
            self.params["false_next"] = str(false_block_id)
    
    def get_branch(self, condition_result: bool) -> int:
        """Возвращает ID следующего блока в зависимости от результата условия"""
        return self.true_branch_id if condition_result else self.false_branch_id