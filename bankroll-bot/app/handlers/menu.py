from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from ..keyboards import main_menu_kb

router = Router()


@router.callback_query(lambda c: c.data and c.data.startswith("menu:"))
async def on_menu(cb: CallbackQuery):
    text = "Что делаем?"
    kb = main_menu_kb()

    try:
        # Если текст уже такой же — проверяем только клавиатуру
        if (cb.message.text or "") == text:
            current_kb = cb.message.reply_markup.model_dump(by_alias=True, exclude_none=True) if cb.message.reply_markup else None
            new_kb = kb.model_dump(by_alias=True, exclude_none=True) if kb else None

            # Меняем только разметку, если она действительно отличается
            if current_kb != new_kb:
                await cb.message.edit_reply_markup(reply_markup=kb)
            # если всё совпадает — ничего не делаем
        else:
            # Текст отличается — обновляем и текст, и клавиатуру
            await cb.message.edit_text(text, reply_markup=kb)

    except TelegramBadRequest as e:
        # Игнорируем "message is not modified", всё остальное пробрасываем
        if "message is not modified" not in str(e).lower():
            raise

    # Убираем "часики" у пользователя
    await cb.answer()
