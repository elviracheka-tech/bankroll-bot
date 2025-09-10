from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from ..states import RebuyAddonSG
from ..db import AsyncSessionLocal
from ..services import list_active_sessions, add_tx, get_or_create_user
from ..enums import FormatType, TxType
from ..keyboards import active_sessions_kb, main_menu_kb

router = Router()

async def _active_tournaments_options(db, user_id: int) -> list[tuple[int,str]]:
    sessions = await list_active_sessions(db, user_id)
    opts: list[tuple[int,str]] = []
    for s in sessions:
        if s.format == FormatType.MTT:
            title = f"{s.tournament_name or 'Tournament'} • {s.currency}"
            opts.append((s.id, title))
    return opts

@router.callback_query(lambda c: c.data == "menu:rebuy")
async def ask_rebuy_target(cb: CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, cb.from_user.id, cb.from_user.username)
        opts = await _active_tournaments_options(session, user.id)
        if not opts:
            await cb.message.edit_text("Нет активных турниров.", reply_markup=main_menu_kb()); await cb.answer(); return
        await state.set_state(RebuyAddonSG.choose_tournament_for_action)
        await state.update_data(action="REBUY")
        await cb.message.edit_text("Для какого турнира?", reply_markup=active_sessions_kb(opts))
        await cb.answer()

@router.callback_query(lambda c: c.data == "menu:addon")
async def ask_addon_target(cb: CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, cb.from_user.id, cb.from_user.username)
        opts = await _active_tournaments_options(session, user.id)
        if not opts:
            await cb.message.edit_text("Нет активных турниров.", reply_markup=main_menu_kb()); await cb.answer(); return
        await state.set_state(RebuyAddonSG.choose_tournament_for_action)
        await state.update_data(action="ADDON")
        await cb.message.edit_text("Для какого турнира?", reply_markup=active_sessions_kb(opts))
        await cb.answer()

@router.callback_query(RebuyAddonSG.choose_tournament_for_action)
async def do_rebuy_addon(cb: CallbackQuery, state: FSMContext):
    if not cb.data.startswith("as:"):
        await cb.answer(); return
    sid = int(cb.data.split(":",1)[1])
    data = await state.get_data()
    action = data.get("action")
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        from ..models import Session
        user = await get_or_create_user(session, cb.from_user.id, cb.from_user.username)
        s = (await session.execute(select(Session).where(Session.id == sid, Session.user_id == user.id))).scalar_one_or_none()
        if not s:
            await cb.message.edit_text("Сессия не найдена.", reply_markup=main_menu_kb()); await cb.answer(); return
        # Суммы по умолчанию: ребай/аддон = buy_in_amount (без рейка)
        base = float(s.buy_in_amount or 0.0)
        if base < 0:
            base = 0.0
        tx_type = TxType.REBUY if action == "REBUY" else TxType.ADDON
        await add_tx(session, user_id=user.id, bankroll_id=s.bankroll_id, session_id=s.id, tx_type=tx_type, amount=base, currency=s.currency)
        # Обновим счётчики
        if action == "REBUY":
            s.rebuy_count += 1
        else:
            s.addon_count += 1
        await session.commit()
    await state.clear()
    await cb.message.edit_text(f"Добавил {action.capitalize()}: {s.tournament_name or 'Tournament'} • {s.currency} {base}\nВозвращаю в меню.", reply_markup=main_menu_kb())
    await cb.answer()
