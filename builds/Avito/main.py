# main.py
import asyncio
import logging
import configparser
import re
from pathlib import Path
from utils.parser import UPBExecutor

def setup_logging(log_file: str, level: str = 'INFO'):
    logging.basicConfig(
        filename=log_file,
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(levelname)s - %(message)s',
        force=True
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger('').addHandler(console)

def parse_script_line(line: str) -> tuple:
    """
    Парсит строку script.txt с поддержкой:
    - команд (start_session, open_url, ...)
    - --user
    - вложенности (for, if, else) — возвращает тип 'control'
    """
    line = line.strip()
    if not line or line.startswith('#'):
        return None, None, 0

    # Проверяем управляющие конструкции
    if line.startswith('for ') or line.startswith('if ') or line.startswith('else:'):
        return 'control', line, 0

    match = re.match(r'(\w+)\((.*)\)', line)
    if not match:
        return None, None, 0

    cmd = match.group(1)
    args_str = match.group(2)
    params = {}

    if args_str:
        # Ищем --user отдельно
        user_match = re.search(r"--user=['\"]([^'\"]*)['\"]", args_str)
        if user_match:
            params['--user'] = user_match.group(1)
            args_str = re.sub(r"--user=['\"][^'\"]*['\"]", '', args_str)

        # Парсим остальные параметры
        for key, value in re.findall(r'(\w+)=([^,)]+)', args_str):
            value = value.strip().strip('"\'')
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.isdigit():
                value = int(value)
            params[key] = value

    return cmd, params, 0


async def main():
    config = configparser.ConfigParser()
    config.read('config.conf')

    setup_logging(
        config['LOGGING']['log_file'],
        config['LOGGING']['level']
    )
    logger = logging.getLogger(__name__)

    logger.info("=" * 60)
    logger.info("🚀 UPB Parser with CloakBrowser")
    logger.info("=" * 60)

    script_path = config['PATHS']['script_path']
    if not Path(script_path).exists():
        logger.error(f"Script file not found: {script_path}")
        return

    with open(script_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    executor = UPBExecutor(config)

    try:
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            cmd, params, indent = parse_script_line(line)

            # Управляющие конструкции (for, if, else) — пока пропускаем
            if cmd == 'control':
                logger.info(f"▶ [{line_num}] {line[:60]}... (control structure - not yet implemented)")
                continue

            if not cmd:
                logger.warning(f"Line {line_num}: Can't parse: {line}")
                continue

            logger.info(f"▶ [{line_num}] {cmd}")
            result = await executor.execute_block(cmd, params)

            if not result.get('success', True):
                logger.error(f"❌ {cmd} failed: {result.get('error')}")
                break

            if cmd == 'end_session':
                logger.info("Session ended by command")
                break

    except KeyboardInterrupt:
        logger.info("⏹️ Interrupted")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        await executor._cleanup()

    logger.info("🏁 UPB Parser Finished")


if __name__ == '__main__':
    asyncio.run(main())