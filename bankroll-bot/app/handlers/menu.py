from aiogram import Router
from aiogram.types import CallbackQuery
from ..keyboards import main_menu_kb

router = Router()

@router.callback_query(lambda c: c.data and c.data.startswith("menu:"))
async def on_menu(cb: CallbackQuery):
    # Этот хэндлер только обновляет меню (остальные перехватывают свои префиксы)
    await cb.message.edit_text("Что делаем?", reply_markup=main_menu_kb())
    await cb.answer()
