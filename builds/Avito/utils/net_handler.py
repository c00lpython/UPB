# utils/net_handler.py
import logging
import aiohttp
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class NetHandler:
    def __init__(self, config: dict):
        self.config = config
        self.telegram_config = config.get("TELEGRAM", {})

    async def send_telegram_message(self, message: str, parse_mode: str = "HTML") -> Dict[str, Any]:
        bot_token = self.telegram_config.get("bot_token", "")
        chat_id = self.telegram_config.get("chat_id", "")

        if not bot_token or not chat_id:
            return {"success": False, "error": "Missing token or chat_id"}

        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                payload = {"chat_id": chat_id, "text": message}
                if parse_mode:
                    payload["parse_mode"] = parse_mode

                async with session.post(url, json=payload, timeout=30) as response:
                    if response.status == 200:
                        logger.info("📨 Telegram message sent")
                        return {"success": True}
                    error = await response.text()
                    return {"success": False, "error": error}
        except Exception as e:
            logger.error(f"Telegram error: {e}")
            return {"success": False, "error": str(e)}

    async def send_telegram_file(self, file_path: str, caption: str = "") -> Dict[str, Any]:
        bot_token = self.telegram_config.get("bot_token", "")
        chat_id = self.telegram_config.get("chat_id", "")

        if not bot_token or not chat_id:
            return {"success": False, "error": "Missing token or chat_id"}

        file_path = Path(file_path)
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        try:
            async with aiohttp.ClientSession() as session:
                url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
                data = aiohttp.FormData()
                data.add_field("chat_id", chat_id)
                if caption:
                    data.add_field("caption", caption)

                with open(file_path, "rb") as f:
                    data.add_field("document", f, filename=file_path.name)
                    async with session.post(url, data=data, timeout=60) as response:
                        if response.status == 200:
                            logger.info(f"📎 File sent: {file_path.name}")
                            return {"success": True}
                        error = await response.text()
                        return {"success": False, "error": error}
        except Exception as e:
            logger.error(f"Telegram file error: {e}")
            return {"success": False, "error": str(e)}