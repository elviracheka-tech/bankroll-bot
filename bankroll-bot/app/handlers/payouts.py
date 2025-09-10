from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from ..db import AsyncSessionLocal
from ..services import list_active_sessions, get_or_create_user, add_tx, close_session
from ..models import Session
from ..enums import FormatType, TxType
from ..keyboards import active_sessions_kb, main_menu_kb
from ..states import FinishSG

router = Router()

@router.callback_query(lambda c: c.data == "menu:finish")
async def choose_session_to_finish(cb: CallbackQuery, state: FSMContext):
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, cb.from_user.id, cb.from_user.username)
        sessions = await list_active_sessions(session, user.id)
        if not sessions:
            await cb.message.edit_text("Нет активных сессий.", reply_markup=main_menu_kb()); await cb.answer(); return
        opts = []
        for s in sessions:
            if s.format == FormatType.CASH:
                title = f"Cash • {s.limit_text or ''} • {s.currency}"
            else:
                title = f"MTT • {s.tournament_name or 'Tournament'} • {s.currency}"
            opts.append((s.id, title))
        await state.set_state(FinishSG.choose_session)
        await cb.message.edit_text("Что завершаем?", reply_markup=active_sessions_kb(opts))
        await cb.answer()

@router.callback_query(FinishSG.choose_session)
async def picked_session(cb: CallbackQuery, state: FSMContext):
    if not cb.data.startswith("as:"):
        await cb.answer(); return
    sid = int(cb.data.split(":",1)[1])
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, cb.from_user.id, cb.from_user.username)
        s = (await session.execute(select(Session).where(Session.id == sid, Session.user_id == user.id))).scalar_one_or_none()
        if not s:
            await cb.message.edit_text("Сессия не найдена.", reply_markup=main_menu_kb()); await cb.answer(); return
        await state.update_data(session_id=s.id)
        if s.format == FormatType.CASH:
            await state.set_state(FinishSG.input_cashout)
            await cb.message.edit_text("Укажи сумму Cashout:")
        else:
            if s.is_pko:
                from aiogram.utils.keyboard import InlineKeyboardBuilder
                kb = InlineKeyboardBuilder(); kb.button(text="Yes", callback_data="split:yes"); kb.button(text="No", callback_data="split:no")
                await state.set_state(FinishSG.ask_pko_split)
                await cb.message.edit_text("Разделить баунти отдельно от основного выигрыша?", reply_markup=kb.as_markup())
            else:
                await state.set_state(FinishSG.input_total_prize)
                await cb.message.edit_text("Укажи общий payout:")
    await cb.answer()

@router.message(FinishSG.input_cashout)
async def finish_cash(msg: Message, state: FSMContext):
    raw = (msg.text or "").lower().replace(",", ".").strip()
    try:
        cashout = float(raw)
    except Exception:
        await msg.answer("Не получилось распознать сумму. Введи число, например: 173")
        return
    data = await state.get_data()
    sid = data.get("session_id")
    async with AsyncSessionLocal() as session:
        s = (await session.execute(select(Session).where(Session.id == sid))).scalar_one()
        await add_tx(session, user_id=s.user_id, bankroll_id=s.bankroll_id, session_id=s.id, tx_type=TxType.CASHOUT, amount=cashout, currency=s.currency)
        await close_session(session, s)
    await state.clear()
    await msg.answer(
        f"Завершил: Cash {s.limit_text or ''} • {s.currency}\nCashout: {cashout}\nИтог будет учтён в балансе. Поздравляю! 🥳\nВозвращаю в меню.",
        reply_markup=main_menu_kb()
    )

from aiogram.utils.keyboard import InlineKeyboardBuilder

@router.callback_query(FinishSG.ask_pko_split)
async def pko_split(cb: CallbackQuery, state: FSMContext):
    if cb.data == "split:yes":
        await state.set_state(FinishSG.input_bounty)
        await cb.message.edit_text("Сколько баунти?")
    elif cb.data == "split:no":
        await state.set_state(FinishSG.input_total_prize)
        await cb.message.edit_text("Укажи общий payout:")
    await cb.answer()

@router.message(FinishSG.input_bounty)
async def input_bounty(msg: Message, state: FSMContext):
    raw = (msg.text or "").lower().replace(","," .").replace(" ","").replace(" .",".").strip()
    raw = raw.replace(",",".")
    try:
        bounty = float(raw)
    except Exception:
        await msg.answer("Не получилось распознать. Введи число, например: 36")
        return
    await state.update_data(bounty=bounty)
    await state.set_state(FinishSG.input_prize)
    await msg.answer("Сколько основной приз?")

@router.message(FinishSG.input_prize)
async def input_prize(msg: Message, state: FSMContext):
    raw = (msg.text or "").lower().replace(",",".").strip()
    try:
        prize = float(raw)
    except Exception:
        await msg.answer("Не получилось распознать. Введи число, например: 144")
        return
    data = await state.get_data()
    sid = data.get("session_id"); bounty = float(data.get("bounty",0.0))
    async with AsyncSessionLocal() as session:
        s = (await session.execute(select(Session).where(Session.id == sid))).scalar_one()
        if bounty>0:
            await add_tx(session, user_id=s.user_id, bankroll_id=s.bankroll_id, session_id=s.id, tx_type=TxType.BOUNTY, amount=bounty, currency=s.currency)
        await add_tx(session, user_id=s.user_id, bankroll_id=s.bankroll_id, session_id=s.id, tx_type=TxType.PRIZE, amount=prize, currency=s.currency)
        await close_session(session, s)
    await state.clear()
    total = prize + (bounty or 0.0)
    await msg.answer(
        f"Завершил: {s.tournament_name or 'Tournament'} • {s.currency}\nБаунти: {bounty} • Приз: {prize}\nИтог учтён. Поздравляю! 🥳\nВозвращаю в меню.",
        reply_markup=main_menu_kb()
    )

@router.message(FinishSG.input_total_prize)
async def input_total_prize(msg: Message, state: FSMContext):
    raw = (msg.text or "").lower().replace(",",".").strip()
    try:
        total = float(raw)
    except Exception:
        await msg.answer("Не получилось распознать. Введи число, например: 180")
        return
    data = await state.get_data(); sid = data.get("session_id")
    async with AsyncSessionLocal() as session:
        s = (await session.execute(select(Session).where(Session.id == sid))).scalar_one()
        await add_tx(session, user_id=s.user_id, bankroll_id=s.bankroll_id, session_id=s.id, tx_type=TxType.PRIZE, amount=total, currency=s.currency)
        await close_session(session, s)
    await state.clear()
    await msg.answer(
        f"Завершил: {s.tournament_name or 'Tournament'} • {s.currency}\nПэйаут: {total}\nИтог учтён. Поздравляю! 🥳\nВозвращаю в меню.",
        reply_markup=main_menu_kb()
    )
