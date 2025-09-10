from aiogram import Router
from aiogram.types import CallbackQuery
from sqlalchemy import select
from ..db import AsyncSessionLocal
from ..services import get_or_create_user
from ..models import Transaction
from ..keyboards import main_menu_kb

router = Router()

@router.callback_query(lambda c: c.data == "menu:history")
async def show_history(cb: CallbackQuery):
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, cb.from_user.id, cb.from_user.username)
        res = await session.execute(select(Transaction).where(Transaction.user_id == user.id, Transaction.is_deleted == False).order_by(Transaction.at.desc()).limit(10))
        txs = res.scalars().all()
    if not txs:
        await cb.message.edit_text("История пуста.", reply_markup=main_menu_kb()); await cb.answer(); return
    lines = []
    for t in txs:
        lines.append(f"#{t.id} • {t.at:%Y-%m-%d} • {t.type} • {t.currency} {t.amount}")
    await cb.message.edit_text("Последние операции:\n"+"\n".join(lines), reply_markup=main_menu_kb())
    await cb.answer()
