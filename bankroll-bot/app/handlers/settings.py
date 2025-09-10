from aiogram import Router
from aiogram.types import CallbackQuery
from ..keyboards import main_menu_kb

router = Router()

@router.callback_query(lambda c: c.data == "menu:settings")
async def settings_root(cb: CallbackQuery):
    await cb.message.edit_text("Settings (MVP):\n— Менеджер валют для румов/мест добавим отдельным окном.\nПока меняйте через мастер новой сессии.", reply_markup=main_menu_kb())
    await cb.answer()
