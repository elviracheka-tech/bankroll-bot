from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from ..keyboards import main_menu_kb

router = Router()

@router.callback_query(F.data.startswith("menu:"))
async def on_menu(cb: CallbackQuery):
    text = "Что делаем?"
    kb = main_menu_kb()

    # На всякий случай: если callback пришёл без message (редко, но бывает)
    if cb.message is None:
        await cb.answer()
        return

    try:
        if (cb.message.text or "") == text:
            # Сравниваем только разметку, чтобы не ловить "message is not modified"
            current_kb = cb.message.reply_markup.model_dump(by_alias=True, exclude_none=True) if cb.message.reply_markup else None
            new_kb = kb.model_dump(by_alias=True, exclude_none=True) if kb else None

            if current_kb != new_kb:
                await cb.message.edit_reply_markup(reply_markup=kb)
            # если и текст и клавиатура совпадают — ничего не меняем
        else:
            await cb.message.edit_text(text, reply_markup=kb)

    except TelegramBadRequest as e:
        # Игнорируем только точный кейс "message is not modified"
        msg = (getattr(e, "message", "") or str(e)).lower()
        if "message is not modified" not in msg:
            raise

    await cb.answer()

