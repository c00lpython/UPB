# bot_main.py
import asyncio
import logging
import configparser
from telegram.request import HTTPXRequest
from utils.bot import UPBBot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    config = configparser.ConfigParser()
    config.read('config.conf')
    token = config['BOT']['token']
    
    # Создаём request с увеличенными таймаутами
    request = HTTPXRequest(
        connect_timeout=60.0,
        read_timeout=60.0,
        write_timeout=60.0,
    )
    
    bot = UPBBot(token, request)
    await bot.run()

if __name__ == '__main__':
    asyncio.run(main())