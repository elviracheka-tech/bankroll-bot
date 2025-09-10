import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# конфиг не называем "settings", чтобы не конфликтовать с handlers.settings
from .config import Settings as AppSettings
from .db import init_db

# модули с роутерами
from .handlers import (
    start,
    sessions,
    tournaments,
    payouts,
    history,
    report,
    settings as settings_handler,  # алиас, чтобы не путать с конфигом
    menu,  # меню подключим последним, как fallback
)


async def main():
    cfg = AppSettings.load()
    logging.basicConfig(level=getattr(logging, cfg.LOG_LEVEL.upper(), logging.INFO))

    await init_db()

    bot = Bot(
        token=cfg.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # на всякий случай снимаем вебхук и чистим невзятые апдейты
    await bot.delete_webhook(drop_pending_updates=True)

    # порядок важен: сначала узкие роутеры действий, потом меню как fallback
    dp.include_router(start.router)
    dp.include_router(sessions.router)
    dp.include_router(tournaments.router)
    dp.include_router(payouts.router)
    dp.include_router(history.router)
    dp.include_router(report.router)
    dp.include_router(settings_handler.router)
    dp.include_router(menu.router)  # <-- ДОЛЖЕН быть последним

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped")
