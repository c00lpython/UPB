# utils/parser.py
import asyncio
import logging
import re
import random
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from cloakbrowser import launch_persistent_context_async, launch_context_async

logger = logging.getLogger(__name__)


class ProxyManager:
    def __init__(self, config: dict):
        self.enabled = False
        self.proxies = []
        self.current_index = 0
        self.request_count = 0

    def get_next(self) -> Optional[str]:
        return None


class UPBExecutor:
    def __init__(self, config):
        self.config = config
        self.context = None
        self.page = None
        self.session_active = False
        self.project_name = None
        self.username = None
        self.user_id = None
        self.extracted_data = []
        self.variables = {}
        self.profile_path = Path(__file__).parent.parent / 'profile'
        self.proxy_manager = ProxyManager({})

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._cleanup()

    async def _cleanup(self):
        try:
            if self.page:
                await self.page.close()
        except:
            pass
        try:
            if self.context:
                await self.context.close()
        except:
            pass
        self.session_active = False

    async def execute_block(self, command: str, params: dict) -> dict:
        handlers = {
            'start_session': self._start_session,
            'open_url': self._open_url,
            'click': self._click,
            'type_text': self._type_text,
            'scroll': self._scroll,
            'scroll_to_bottom': self._scroll_to_bottom,
            'parse_data': self._parse_data,
            'screenshot': self._screenshot,
            'reload_page': self._reload_page,
            'wait': self._wait,
            'save_data': self._save_data,
            'send_telegram': self._send_telegram,
            'convert_excel': self._convert_excel,
            'end_session': self._end_session,
        }

        handler = handlers.get(command)
        if not handler:
            logger.warning(f"Unknown command: {command}")
            return {'success': False, 'error': f'Unknown command: {command}'}

        try:
            return await handler(params)
        except Exception as e:
            logger.error(f"Command {command} failed: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    async def _start_session(self, params: dict) -> dict:
        project = params.get('project', 'UPBParser')
        headless = params.get('headless', False)
        timeout = params.get('timeout', 30)
        username = params.get('--user', None)

        logger.info(f"🚀 Starting CloakBrowser session: {project}")
        if username:
            logger.info(f"👤 User: {username}")

        self.project_name = project
        self.username = username
        self.user_id = None

        if username:
            try:
                from utils.db_handler import UserDB
                user = UserDB.get_user_by_username(username)
                if user:
                    self.user_id = user["id"]
                    logger.info(f"✅ User found: {username} (ID: {self.user_id})")
                else:
                    logger.warning(f"⚠️ User '{username}' NOT found in DB!")
            except Exception as e:
                logger.warning(f"⚠️ Could not verify user: {e}")

        viewports = [
            {'width': 1920, 'height': 1080},
            {'width': 1366, 'height': 768},
            {'width': 1536, 'height': 864},
        ]
        viewport = random.choice(viewports) if not headless else None

        try:
            if self.profile_path.exists() and not headless:
                logger.info(f"📁 Loading profile from: {self.profile_path}")
                self.context = await launch_persistent_context_async(
                    user_data_dir=str(self.profile_path),
                    headless=headless,
                    viewport=viewport,
                    geoip=True,
                    humanize=True,
                    locale='ru-RU',
                    timezone_id='Europe/Moscow',
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36'
                )
                self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            else:
                logger.info("🆕 Starting fresh browser")
                self.context = await launch_context_async(
                    headless=headless,
                    viewport=viewport,
                    geoip=True,
                    humanize=True,
                    locale='ru-RU',
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                self.page = await self.context.new_page()

            self.session_active = True
            logger.info(f"✅ CloakBrowser ready (humanize=True)")
            return {'success': True, 'project': project}

        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            await self._cleanup()
            return {'success': False, 'error': str(e)}

    async def _open_url(self, params: dict) -> dict:
        url = params.get('url', '')
        wait_strategy = params.get('wait', 'domcontentloaded')
        timeout = params.get('timeout', 30000)

        if not url:
            return {'success': False, 'error': 'No URL'}

        logger.info(f"🌐 Opening URL: {url}")
        try:
            await asyncio.sleep(random.uniform(0.3, 0.8))
            await self.page.goto(url, timeout=timeout, wait_until=wait_strategy)
            title = await self.page.title()
            logger.info(f"   Loaded: {title[:60]}...")
            return {'success': True, 'url': url}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _click(self, params: dict) -> dict:
        selector = params.get('selector', '')
        selector_type = params.get('type', 'css')
        count = params.get('count', 1)
        wait_after = params.get('wait', 1000)

        if not selector:
            return {'success': False, 'error': 'No selector'}

        playright_selector = self._to_playwright_selector(selector, selector_type)
        logger.info(f"🖱️ Clicking: {selector}")

        try:
            await self.page.wait_for_selector(playright_selector, timeout=10000)
            for _ in range(count):
                await self.page.click(playright_selector)
                await asyncio.sleep(random.uniform(0.3, 0.7))
            if wait_after:
                await asyncio.sleep(wait_after / 1000)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _type_text(self, params: dict) -> dict:
        selector = params.get('selector', '')
        selector_type = params.get('type', 'css')
        text = params.get('text', '')
        clear_first = params.get('clear', True)
        press_enter = params.get('enter', False)
        delay = params.get('delay', 0)

        if not selector:
            return {'success': False, 'error': 'No selector'}

        playright_selector = self._to_playwright_selector(selector, selector_type)
        logger.info(f"⌨️ Typing into: {selector}")

        try:
            await self.page.wait_for_selector(playright_selector, timeout=10000)
            if clear_first:
                await self.page.fill(playright_selector, '')
                await asyncio.sleep(random.uniform(0.1, 0.3))
            await self.page.type(playright_selector, text, delay=delay if delay else random.randint(30, 80))
            if press_enter:
                await asyncio.sleep(random.uniform(0.2, 0.5))
                await self.page.keyboard.press('Enter')
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _scroll(self, params: dict) -> dict:
        direction = params.get('direction', 'down')
        amount = params.get('amount', 500)
        wait_after = params.get('wait', 1000)
        selector = params.get('selector', '')

        if not self.page:
            return {'success': False, 'error': 'No active page'}

        try:
            if selector:
                element = await self.page.query_selector(selector)
                if element:
                    await element.scroll_into_view_if_needed()
                    logger.info(f"📜 Scrolled to element: {selector}")
            else:
                scroll_amount = amount if direction == 'down' else -amount
                steps = random.randint(10, 25)
                step_scroll = scroll_amount / steps
                for _ in range(steps):
                    await self.page.evaluate(f"window.scrollBy(0, {step_scroll})")
                    await asyncio.sleep(random.uniform(0.02, 0.08))
                logger.info(f"📜 Scrolled {direction} by {amount}px")

            if wait_after:
                await asyncio.sleep(wait_after / 1000)
            return {'success': True}
        except Exception as e:
            logger.error(f"Failed to scroll: {e}")
            return {'success': False, 'error': str(e)}

    async def _scroll_to_bottom(self, params: dict) -> dict:
        wait_after = params.get('wait', 1000)
        max_attempts = params.get('max_attempts', 10)

        logger.info("📜 Scrolling to bottom of page...")

        try:
            previous_height = 0
            for attempt in range(max_attempts):
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(wait_after / 1000)

                new_height = await self.page.evaluate("document.body.scrollHeight")
                if new_height == previous_height:
                    logger.info(f"📜 Reached bottom after {attempt + 1} attempts")
                    break

                previous_height = new_height
                logger.debug(f"📜 Attempt {attempt + 1}: scrollHeight = {new_height}")

            if wait_after:
                await asyncio.sleep(wait_after / 1000)

            return {'success': True, 'attempts': attempt + 1}

        except Exception as e:
            logger.error(f"Failed to scroll to bottom: {e}")
            return {'success': False, 'error': str(e)}

    async def _parse_data(self, params: dict) -> dict:
        var_name = params.get('var', '')
        save_to = params.get('save_to', 'result')
        extract_type = params.get('extract', 'text')
        attribute = params.get('attribute', '')

        if not var_name:
            return {'success': False, 'error': 'No var name'}

        if not self.page:
            return {'success': False, 'error': 'No active page'}

        selector = var_name

        try:
            await self.page.wait_for_selector(selector, timeout=10000)
            elements = await self.page.query_selector_all(selector)
            if not elements:
                return {'success': False, 'error': f'Element not found: {selector}'}

            values = []
            for element in elements[:30]:
                if extract_type == 'text':
                    value = await element.inner_text()
                elif extract_type == 'html':
                    value = await element.inner_html()
                elif extract_type == 'attribute' and attribute:
                    value = await element.get_attribute(attribute)
                else:
                    value = await element.inner_text()
                values.append(value.strip())

            self.variables[save_to] = values

            for val in values:
                self.extracted_data.append({
                    'var': var_name,
                    'value': val,
                    'timestamp': datetime.now().isoformat()
                })

            logger.info(f"📊 Extracted {len(values)} items from '{var_name}'")
            return {'success': True, 'values': values, 'count': len(values)}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _screenshot(self, params: dict) -> dict:
        filename = params.get('filename', 'screenshot.png')
        full_page = params.get('full', False)
        selector = params.get('selector', '')

        if not self.page:
            return {'success': False, 'error': 'No active page'}

        results_dir = Path('results') / (self.project_name or 'default')
        results_dir.mkdir(parents=True, exist_ok=True)
        filepath = results_dir / filename

        logger.info(f"📸 Screenshot: {filepath}")

        try:
            if selector:
                element = await self.page.query_selector(selector)
                if element:
                    await element.screenshot(path=str(filepath))
                else:
                    await self.page.screenshot(path=str(filepath), full_page=full_page)
            else:
                await self.page.screenshot(path=str(filepath), full_page=full_page)
            logger.info(f"   Saved")
            return {'success': True, 'filename': str(filepath)}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _reload_page(self, params: dict) -> dict:
        wait_ms = params.get('wait', 2000)
        try:
            await self.page.reload()
            if wait_ms:
                await asyncio.sleep(wait_ms / 1000)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _wait(self, params: dict) -> dict:
        seconds = params.get('seconds', 2)
        actual_seconds = seconds * random.uniform(0.85, 1.15)
        logger.info(f"⏳ Waiting {actual_seconds:.1f}s...")
        await asyncio.sleep(actual_seconds)
        return {'success': True}

    async def _save_data(self, params: dict) -> dict:
        from utils.output_handler import OutputHandler

        output_path = params.get('path', './output')
        if not self.extracted_data:
            return {'success': False, 'error': 'No data to save'}

        formats = ["excel"]
        if self.config.has_section("OUTPUT"):
            try:
                formats_str = self.config.get("OUTPUT", "formats", fallback="excel")
                formats = [f.strip() for f in formats_str.split(",")]
            except:
                formats = ["excel"]

        result = OutputHandler.save_results(
            data=self.extracted_data,
            project_name=self.project_name,
            user_id=self.user_id,
            output_path=output_path,
            formats=formats
        )
        return result

    async def _send_telegram(self, params: dict) -> dict:
        from utils.net_handler import NetHandler

        net = NetHandler({"TELEGRAM": {
            "bot_token": params.get('token', ''),
            "chat_id": params.get('chat', ''),
        }})

        message = params.get('msg', '').replace('{count}', str(len(self.extracted_data))).replace('{project}', str(self.project_name or 'Unknown'))
        return await net.send_telegram_message(message, params.get('parse', ''))

    async def _convert_excel(self, params: dict) -> dict:
        """convert_excel(input='...', format='csv', output='...', sheet='Sheet1')"""
        from utils.output_handler import OutputHandler

        input_file = params.get('input', '')
        output_format = params.get('format', 'csv')
        output_file = params.get('output', '')
        sheet_name = params.get('sheet', 'Sheet1')

        if not input_file:
            return {'success': False, 'error': 'No input file'}

        try:
            # Проверяем существование файла
            input_path = Path(input_file)
            if not input_path.exists():
                # Пробуем найти в папке пользователя
                if self.user_id:
                    user_input = Path('results') / f"user_{self.user_id}" / input_file
                    if user_input.exists():
                        input_path = user_input
                    else:
                        return {'success': False, 'error': f'File not found: {input_file}'}

            result = OutputHandler.convert_excel(
                input_file=str(input_path),
                output_format=output_format,
                output_file=output_file,
                sheet_name=sheet_name
            )
            return result
        except Exception as e:
            logger.error(f"Convert Excel failed: {e}")
            return {'success': False, 'error': str(e)}

    async def _end_session(self, params: dict) -> dict:
        close_browser = params.get('close', True)
        logger.info("🏁 Ending session")

        if self.config.has_section("TELEGRAM"):
            try:
                send_on_success = self.config.getboolean("TELEGRAM", "send_on_success", fallback=False)
                if send_on_success and self.extracted_data:
                    from utils.net_handler import NetHandler
                    tg_config = dict(self.config.items("TELEGRAM"))
                    net = NetHandler({"TELEGRAM": tg_config})
                    await net.send_telegram_message(
                        f"✅ Парсинг {self.project_name} завершён!\n📊 Собрано: {len(self.extracted_data)} записей"
                    )
            except Exception as e:
                logger.warning(f"Could not send Telegram notification: {e}")

        if close_browser:
            await self._cleanup()

        return {'success': True, 'data_collected': len(self.extracted_data)}

    def _to_playwright_selector(self, selector: str, selector_type: str) -> str:
        if selector_type == 'xpath':
            return f'xpath={selector}'
        elif selector_type == 'text':
            return f'text="{selector}"'
        return selector