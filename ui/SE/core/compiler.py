import json
import os
from typing import Dict, List, Any, Optional


class UPBCompiler:
    """Компилятор workflow в script.txt"""
    
    def __init__(self, workflow_path: str, variables=None):
        self.workflow_path = workflow_path
        self.variables_dict = {}
        self.blocks = {}
        self.connections = []
        
        self._load_workflow()
        self._load_variables(variables)
    
    def _load_workflow(self):
        with open(self.workflow_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        blocks_data = data.get('blocks', {})
        for block_id_str, block_data in blocks_data.items():
            block_id = int(block_id_str)
            self.blocks[block_id] = {
                'id': block_id,
                'type': block_data['node_type'],
                'name': block_data['name'],
                'params': block_data.get('params', {}),
                'position': block_data.get('position', {'x': 0, 'y': 0})
            }
        
        connections_data = data.get('connections', {})
        
        if isinstance(connections_data, dict):
            for conn_id, conn_data in connections_data.items():
                if isinstance(conn_data, dict):
                    self.connections.append({
                        'id': conn_id,
                        'from_block_id': conn_data.get('from_block_id'),
                        'from_port': conn_data.get('from_port'),
                        'to_block_id': conn_data.get('to_block_id'),
                        'to_port': conn_data.get('to_port')
                    })
        elif isinstance(connections_data, list):
            for conn in connections_data:
                if isinstance(conn, dict):
                    self.connections.append({
                        'from_block_id': conn.get('from_block_id'),
                        'from_port': conn.get('from_port'),
                        'to_block_id': conn.get('to_block_id'),
                        'to_port': conn.get('to_port')
                    })
        
        print(f"🔗 Загружено {len(self.connections)} соединений")
    
    def _load_variables(self, variables):
        self.variables_dict = {}
        
        if variables is None:
            return
        
        if isinstance(variables, dict):
            self.variables_dict = variables
            print(f"📦 Загружено {len(self.variables_dict)} переменных из словаря")
            return
        
        if isinstance(variables, str) and os.path.exists(variables):
            try:
                import pandas as pd
                df = pd.read_excel(variables)
                for _, row in df.iterrows():
                    name = row.get('Name')
                    if name and not pd.isna(name):
                        name_str = str(name).strip()
                        self.variables_dict[name_str] = {
                            'selector': str(row.get('XPath/CSS', '')) if not pd.isna(row.get('XPath/CSS', '')) else '',
                            'url': str(row.get('URL', '')) if not pd.isna(row.get('URL', '')) else '',
                            'type': str(row.get('Type', 'Static')) if not pd.isna(row.get('Type', 'Static')) else 'Static',
                            'sample': str(row.get('Sample Text', '')) if not pd.isna(row.get('Sample Text', '')) else ''
                        }
                print(f"📦 Загружено {len(self.variables_dict)} переменных из {variables}")
            except Exception as e:
                print(f"⚠️ Ошибка загрузки переменных: {e}")
    
    def _resolve_value(self, value: str) -> str:
        if not value or not isinstance(value, str):
            return f"'{value}'" if value else "''"
        
        if value in self.variables_dict:
            var_data = self.variables_dict[value]
            if var_data.get('url') and var_data['url'].strip():
                return f"parseValue('{value}', 'url')"
            if var_data.get('selector') and var_data['selector'].strip():
                return f"parseValue('{value}', 'selector')"
        
        if value.startswith(('"', "'")):
            return value
        
        return f"'{value}'"
    
    def _compile_condition(self, condition_data: dict) -> str:
        condition_str = condition_data.get('condition', '')
        variables = condition_data.get('variables', {})
        
        if not condition_str:
            return "True"
        
        result = condition_str
        for var_name, var_value in variables.items():
            if isinstance(var_value, str):
                if var_value in self.variables_dict:
                    var_value = f"parseValue('{var_value}', 'selector')"
                else:
                    var_value = f"'{var_value}'"
            result = result.replace(var_name, str(var_value))
        
        return result
    
    def _compile_command(self, block: dict) -> str:
        btype = block['type']
        p = block['params']
        
        templates = {
            'startofwork': "start_session(project='{project}', headless={headless}, timeout={timeout})",
            'openurl': "open_url(url={url}, wait='{wait}', timeout={timeout})",
            'click': "click(selector={selector}, type='{type}', count={count}, wait={wait})",
            'type': "type_text(selector={selector}, type='{type}', text='{text}', clear={clear}, enter={enter}, delay={delay})",
            'parsedata': "parse_data(var='{var}', save_to='{save}', extract='{extract}', attribute='{attr}')",
            'screenshot': "screenshot(filename='{filename}', full={full}, selector={selector})",
            'convertexcel': "convert_excel(input='{input}', format='{format}', output='{output}', sheet='{sheet}')",
            'forloop': "for {iterator} in {iterable}:",
            'reload': "reload_page(wait={wait}, nocache={nocache})",
            'sendtelegram': "send_telegram(token='{token}', chat='{chat}', msg='{msg}', parse='{parse}')",
            'savedata': "save_data(data={data}, format='{format}', path='{path}', overwrite={overwrite})",
            'endsession': "end_session(save={save}, close={close}, report={report})",
        }
        
        if btype == 'if':
            condition_data = p.get('condition_data', {})
            if condition_data:
                condition = self._compile_condition(condition_data)
            else:
                left = p.get('left', '')
                op = p.get('operator', 'eq')
                right = p.get('right', '')
                
                left_val = self._resolve_value(left)
                right_val = self._resolve_value(right)
                
                op_map = {
                    'eq': '==', 'ne': '!=', 'gt': '>', 'lt': '<',
                    'contains': 'in', 'startswith': '.startswith', 'endswith': '.endswith'
                }
                
                if op == 'contains':
                    condition = f"{right_val} in {left_val}"
                elif op == 'startswith':
                    condition = f"{left_val}.startswith({right_val})"
                elif op == 'endswith':
                    condition = f"{left_val}.endswith({right_val})"
                else:
                    condition = f"{left_val} {op_map[op]} {right_val}"
            
            return f"if {condition}:"
        
        if btype not in templates:
            return f"# TODO: {btype}"
        
        args = {
            'project': p.get('projectName', ''),
            'headless': p.get('headless', True),
            'timeout': p.get('timeout', 30),
            'url': self._resolve_value(p.get('url', '')),
            'wait': p.get('waitStrategy', 'load'),
            'selector': self._resolve_value(p.get('selector', '')),
            'type': p.get('selectorType', 'css'),
            'count': p.get('clickCount', 1),
            'wait': p.get('waitAfter', 1000),
            'text': p.get('text', ''),
            'clear': p.get('clearFirst', True),
            'enter': p.get('pressEnter', False),
            'delay': p.get('delay', 0),
            'var': p.get('varName', ''),
            'save': p.get('saveTo', 'result'),
            'extract': p.get('extractType', 'text'),
            'attr': p.get('attributeName', ''),
            'filename': p.get('filename', 'screenshot.png'),
            'full': p.get('fullPage', False),
            'input': p.get('inputFile', ''),
            'format': p.get('outputFormat', 'csv'),
            'output': p.get('outputFile', ''),
            'sheet': p.get('sheetName', 'Sheet1'),
            'iterator': p.get('iterator', 'item'),
            'iterable': p.get('iterable', '[]'),
            'nocache': p.get('ignoreCache', True),
            'token': p.get('botToken', ''),
            'chat': p.get('chatId', ''),
            'msg': p.get('message', ''),
            'parse': p.get('parseMode', ''),
            'data': self._resolve_value(p.get('dataVar', '')),
            'path': p.get('outputPath', './output'),
            'overwrite': p.get('overwrite', True),
            'save': p.get('saveResults', True),
            'close': p.get('closeBrowser', True),
            'report': p.get('exportReport', False),
        }
        
        try:
            return templates[btype].format(**args)
        except KeyError as e:
            return f"# ERROR: missing key {e} in {btype}"
    
    def _find_start_block(self) -> Optional[int]:
        for block_id, block in self.blocks.items():
            if block['type'] == 'startofwork':
                return block_id
        return None
    
    def _get_branch_block(self, block_id: int, branch: str) -> Optional[int]:
        """Возвращает блок для конкретной ветки IfBlock (true/false)"""
        for conn in self.connections:
            if conn.get('from_block_id') == block_id and conn.get('from_port') == branch:
                return conn.get('to_block_id')
        return None
    
    def _get_next_block(self, block_id: int) -> Optional[int]:
        """Возвращает следующий блок по соединению (не true/false порты)"""
        for conn in self.connections:
            from_port = conn.get('from_port')
            if conn.get('from_block_id') == block_id and from_port not in ('true', 'false', 'center'):
                return conn.get('to_block_id')
        return None
    
    def compile_chain(self) -> str:
        """
        Компилирует workflow, поддерживая if/else ветвление
        """
        start_id = self._find_start_block()
        if not start_id:
            return "# ERROR: No startofwork block found"
        
        commands = []
        visited = set()
        
        def traverse(block_id: int, indent_level: int = 0):
            """Рекурсивный обход с поддержкой if/else"""
            if block_id is None or block_id in visited:
                return
            
            block = self.blocks.get(block_id)
            if not block:
                return
            
            visited.add(block_id)
            
            cmd = self._compile_command(block)
            indent = "    " * indent_level
            commands.append(f"{indent}{cmd}")
            
            if block['type'] == 'if':
                true_next = self._get_branch_block(block_id, 'true')
                false_next = self._get_branch_block(block_id, 'false')
                
                # Обрабатываем true ветку
                if true_next:
                    traverse(true_next, indent_level + 1)
                
                # Обрабатываем false ветку (else)
                if false_next:
                    commands.append(f"{indent}else:")
                    traverse(false_next, indent_level + 1)
            
            elif block['type'] == 'endsession':
                pass
            
            else:
                next_id = self._get_next_block(block_id)
                if next_id:
                    traverse(next_id, indent_level)
        
        traverse(start_id)
        return '\n'.join(commands)
    
    def compile(self, mode: str = "chain") -> str:
        if mode == "chain":
            return self.compile_chain()
        else:
            commands = []
            sorted_blocks = sorted(self.blocks.values(), key=lambda b: b['position']['y'])
            for block in sorted_blocks:
                cmd = self._compile_command(block)
                if cmd:
                    commands.append(cmd)
            return '\n'.join(commands)
    
    def save(self, output_path: str, mode: str = "chain"):
        script = self.compile(mode)
        
        header = f"""# UPB Generated Script
# Mode: {mode}
# Blocks: {len(self.blocks)}
# Connections: {len(self.connections)}

"""
        full_script = header + script
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_script)
        
        print(f"✅ Script saved to {output_path}")


def compile_workflow(workflow_path: str, output_path: str, variables=None, mode: str = "chain"):
    compiler = UPBCompiler(workflow_path, variables)
    compiler.save(output_path, mode)