from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
from ..states import ReportSG
from ..keyboards import currencies_kb, main_menu_kb
from ..services import report_stats, get_or_create_user
from ..db import AsyncSessionLocal
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.callback_query(lambda c: c.data == "menu:report")
async def report_pick_currency(cb: CallbackQuery, state: FSMContext):
    await state.set_state(ReportSG.choose_currency)
    await cb.message.edit_text("Выбери валюту отчёта:", reply_markup=currencies_kb())
    await cb.answer()

@router.callback_query(ReportSG.choose_currency)
async def report_pick_period(cb: CallbackQuery, state: FSMContext):
    if not cb.data.startswith("cur:"):
        await cb.answer(); return
    code = cb.data.split(":",1)[1]
    if code == "__OTHER__":
        code = "USD"
    await state.update_data(report_currency=code)
    kb = InlineKeyboardBuilder()
    kb.button(text="📅 Week", callback_data="rp:week")
    kb.button(text="📆 Month", callback_data="rp:month")
    kb.button(text="📊 Year", callback_data="rp:year")
    kb.button(text="🎯 Custom", callback_data="rp:custom")
    kb.button(text="⬅️ Back", callback_data="back")
    kb.button(text="✖️ Cancel", callback_data="cancel")
    kb.adjust(2,2,2)
    await state.set_state(ReportSG.choose_period)
    await cb.message.edit_text("Выбери период:", reply_markup=kb.as_markup())
    await cb.answer()

@router.callback_query(ReportSG.choose_period)
async def report_period(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    code = data.get("report_currency","USD")
    now = datetime.utcnow()
    if cb.data == "rp:week":
        start = now - timedelta(days=7)
        end = now
    elif cb.data == "rp:month":
        start = now - timedelta(days=30)
        end = now
    elif cb.data == "rp:year":
        start = now - timedelta(days=365)
        end = now
    elif cb.data == "rp:custom":
        await state.set_state(ReportSG.input_custom_from)
        await cb.message.edit_text("Введи дату начала в формате YYYY-MM-DD:")
        await cb.answer(); return
    elif cb.data == "back":
        await state.set_state(ReportSG.choose_currency)
        await cb.message.edit_text("Выбери валюту отчёта:", reply_markup=currencies_kb()); await cb.answer(); return
    elif cb.data == "cancel":
        await state.clear(); await cb.message.edit_text("Отменено.", reply_markup=main_menu_kb()); await cb.answer(); return
    else:
        await cb.answer(); return

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, cb.from_user.id, cb.from_user.username)
        stats = await report_stats(session, user.id, code, start, end)
    await state.clear()
    await cb.message.edit_text(
        f"Отчёт: {code}\nСессий: {stats['sessions']}\nПрофит: {stats['profit']}\nСредний / сессия: {stats['avg_per_session']}",
        reply_markup=main_menu_kb()
    )
    await cb.answer()

@router.message(ReportSG.input_custom_from)
async def report_custom_from(msg: Message, state: FSMContext):
    try:
        dt = datetime.strptime(msg.text.strip(), "%Y-%m-%d")
    except Exception:
        await msg.answer("Формат даты: YYYY-MM-DD. Попробуй ещё раз:")
        return
    await state.update_data(custom_from=dt)
    await state.set_state(ReportSG.input_custom_to)
    await msg.answer("Теперь введи дату конца в формате YYYY-MM-DD:")

@router.message(ReportSG.input_custom_to)
async def report_custom_to(msg: Message, state: FSMContext):
    try:
        dt2 = datetime.strptime(msg.text.strip(), "%Y-%m-%d")
    except Exception:
        await msg.answer("Формат даты: YYYY-MM-DD. Попробуй ещё раз:")
        return
    data = await state.get_data()
    start = data.get("custom_from")
    end = dt2
    code = data.get("report_currency","USD")
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, msg.from_user.id, msg.from_user.username)
        stats = await report_stats(session, user.id, code, start, end)
    await state.clear()
    await msg.answer(
        f"Отчёт: {code}\nПериод: {start:%Y-%m-%d} — {end:%Y-%m-%d}\nСессий: {stats['sessions']}\nПрофит: {stats['profit']}\nСредний / сессия: {stats['avg_per_session']}",
        reply_markup=main_menu_kb()
    )
