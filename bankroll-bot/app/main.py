import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from .config import Settings
from .db import init_db
from .handlers import start, menu, sessions, tournaments, payouts, history, report, settings

async def main():
    settings = Settings.load()
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

    await init_db()

    bot = Bot(token=settings.TELEGRAM_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Подключаем роутеры
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(sessions.router)
    dp.include_router(tournaments.router)
    dp.include_router(payouts.router)
    dp.include_router(history.router)
    dp.include_router(report.router)
    dp.include_router(settings.router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped")
