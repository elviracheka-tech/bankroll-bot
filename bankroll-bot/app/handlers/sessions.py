from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from ..states import NewSessionSG
from ..keyboards import venue_kb, format_kb, game_kb, rooms_kb, currencies_kb, main_menu_kb
from ..enums import VenueType, FormatType, GameVariant
from ..services import get_or_create_user, list_bankrolls, create_bankroll, get_or_create_room, get_or_create_place
from ..db import AsyncSessionLocal
from ..utils import ROOMS
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.callback_query(lambda c: c.data == "menu:new_session")
async def start_new_session(cb: CallbackQuery, state: FSMContext):
    await state.set_state(NewSessionSG.choose_venue)
    await cb.message.edit_text("Начнём новую сессию! 🎲\nСначала выбери тип:", reply_markup=venue_kb())
    await cb.answer()

@router.callback_query(NewSessionSG.choose_venue)
async def choose_venue(cb: CallbackQuery, state: FSMContext):
    if cb.data == "venue:ONLINE":
        await state.update_data(venue=VenueType.ONLINE)
    elif cb.data == "venue:OFFLINE":
        await state.update_data(venue=VenueType.OFFLINE)
    elif cb.data == "cancel":
        await state.clear(); await cb.message.edit_text("Отменено.", reply_markup=main_menu_kb()); await cb.answer(); return
    else:
        await cb.answer(); return
    await state.set_state(NewSessionSG.choose_format)
    await cb.message.edit_text("Формат игры:", reply_markup=format_kb())

@router.callback_query(NewSessionSG.choose_format)
async def choose_format(cb: CallbackQuery, state: FSMContext):
    if cb.data == "format:CASH":
        await state.update_data(format=FormatType.CASH)
    elif cb.data == "format:MTT":
        await state.update_data(format=FormatType.MTT)
    elif cb.data == "back":
        await state.set_state(NewSessionSG.choose_venue)
        await cb.message.edit_text("Сначала выбери тип:", reply_markup=venue_kb()); await cb.answer(); return
    elif cb.data == "cancel":
        await state.clear(); await cb.message.edit_text("Отменено.", reply_markup=main_menu_kb()); await cb.answer(); return
    else:
        await cb.answer(); return
    await state.set_state(NewSessionSG.choose_game)
    await cb.message.edit_text("Выбери дисциплину:", reply_markup=game_kb())

@router.callback_query(NewSessionSG.choose_game)
async def choose_game(cb: CallbackQuery, state: FSMContext):
    if cb.data.startswith("game:"):
        code = cb.data.split(":",1)[1]
        if code == "OTHER":
            await state.set_state(NewSessionSG.input_game_name)
            await cb.message.edit_text("Введи название игры (например, 6+ Holdem):")
            await cb.answer(); return
        await state.update_data(game=GameVariant[code])
    elif cb.data == "back":
        await state.set_state(NewSessionSG.choose_format)
        await cb.message.edit_text("Формат игры:", reply_markup=format_kb()); await cb.answer(); return
    elif cb.data == "cancel":
        await state.clear(); await cb.message.edit_text("Отменено.", reply_markup=main_menu_kb()); await cb.answer(); return
    else:
        await cb.answer(); return
    data = await state.get_data()
    if data.get("venue") == VenueType.ONLINE:
        await state.set_state(NewSessionSG.choose_room)
        await cb.message.edit_text("Выбери рум:", reply_markup=rooms_kb())
    else:
        await state.set_state(NewSessionSG.choose_place)
        await cb.message.edit_text("Выбери место (клуб/зал) или добавь своё:", reply_markup=rooms_kb())

@router.message(NewSessionSG.input_game_name)
async def input_game_name(msg: Message, state: FSMContext):
    text = (msg.text or "").strip()
    if not text:
        await msg.answer("Название не должно быть пустым. Введи ещё раз:")
        return
    await state.update_data(game="OTHER", game_name=text[:100])
    data = await state.get_data()
    if data.get("venue") == VenueType.ONLINE:
        await state.set_state(NewSessionSG.choose_room)
        await msg.answer("Выбери рум:", reply_markup=rooms_kb())
    else:
        await state.set_state(NewSessionSG.choose_place)
        await msg.answer("Выбери место (клуб/зал) или добавь своё:", reply_markup=rooms_kb())

@router.callback_query(NewSessionSG.choose_room)
async def choose_room(cb: CallbackQuery, state: FSMContext):
    if cb.data == "back":
        await state.set_state(NewSessionSG.choose_game)
        await cb.message.edit_text("Выбери дисциплину:", reply_markup=game_kb()); await cb.answer(); return
    if cb.data == "cancel":
        await state.clear(); await cb.message.edit_text("Отменено.", reply_markup=main_menu_kb()); await cb.answer(); return

    _, val = cb.data.split(":",1)
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, cb.from_user.id, cb.from_user.username)
        if val == "__OTHER__":
            await state.set_state(NewSessionSG.input_room_other)
            await cb.message.edit_text("Введи название рума:")
            await cb.answer(); return
        room = await get_or_create_room(session, user.id, val)
        await state.update_data(room_id=room.id, room_name=room.name)
    await state.set_state(NewSessionSG.choose_currency)
    await cb.message.edit_text(f"Выбери валюту для {val} (я запомню):", reply_markup=currencies_kb())
    await cb.answer()

@router.message(NewSessionSG.input_room_other)
async def input_room_other(msg: Message, state: FSMContext):
    name = (msg.text or "").strip()[:100]
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, msg.from_user.id, msg.from_user.username)
        room = await get_or_create_room(session, user.id, name)
        await state.update_data(room_id=room.id, room_name=room.name)
    await state.set_state(NewSessionSG.choose_currency)
    await msg.answer(f"Выбери валюту для {name} (я запомню):", reply_markup=currencies_kb())

@router.callback_query(NewSessionSG.choose_place)
async def choose_place(cb: CallbackQuery, state: FSMContext):
    # Для MVP используем тот же список UI, но логически это места
    if cb.data == "back":
        await state.set_state(NewSessionSG.choose_game)
        await cb.message.edit_text("Выбери дисциплину:", reply_markup=game_kb()); await cb.answer(); return
    if cb.data == "cancel":
        await state.clear(); await cb.message.edit_text("Отменено.", reply_markup=main_menu_kb()); await cb.answer(); return

    _, val = cb.data.split(":",1)
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, cb.from_user.id, cb.from_user.username)
        if val == "__OTHER__":
            await state.set_state(NewSessionSG.input_place_other)
            await cb.message.edit_text("Введи название места (клуб/зал):")
            await cb.answer(); return
        place = await get_or_create_place(session, user.id, val)
        await state.update_data(place_id=place.id, place_name=place.name)
    await state.set_state(NewSessionSG.choose_currency)
    await cb.message.edit_text(f"Выбери валюту для {val} (я запомню):", reply_markup=currencies_kb())
    await cb.answer()

@router.message(NewSessionSG.input_place_other)
async def input_place_other(msg: Message, state: FSMContext):
    name = (msg.text or "").strip()[:100]
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, msg.from_user.id, msg.from_user.username)
        place = await get_or_create_place(session, user.id, name)
        await state.update_data(place_id=place.id, place_name=place.name)
    await state.set_state(NewSessionSG.choose_currency)
    await msg.answer(f"Выбери валюту для {name} (я запомню):", reply_markup=currencies_kb())

@router.callback_query(NewSessionSG.choose_currency)
async def choose_currency(cb: CallbackQuery, state: FSMContext):
    if cb.data == "back":
        data = await state.get_data()
        if data.get("room_id"):
            await state.set_state(NewSessionSG.choose_room)
            await cb.message.edit_text("Выбери рум:", reply_markup=rooms_kb()); await cb.answer(); return
        else:
            await state.set_state(NewSessionSG.choose_place)
            await cb.message.edit_text("Выбери место:", reply_markup=rooms_kb()); await cb.answer(); return
    if cb.data == "cancel":
        await state.clear(); await cb.message.edit_text("Отменено.", reply_markup=main_menu_kb()); await cb.answer(); return

    if not cb.data.startswith("cur:"):
        await cb.answer(); return
    code = cb.data.split(":",1)[1]
    if code == "__OTHER__":
        code = "USD"  # MVP: по умолчанию USD
    await state.update_data(currency=code)

    # Выбор/создание банкролла в этой валюте
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, cb.from_user.id, cb.from_user.username)
        brs = await list_bankrolls(session, user.id, currency=code)
        if not brs:
            br = await create_bankroll(session, user.id, name=f"Default {code}", currency=code, make_default=True)
            await state.update_data(bankroll_id=br.id)
        else:
            await state.update_data(bankroll_id=brs[0].id)

    data = await state.get_data()
    if data.get("format") == FormatType.MTT:
        await state.set_state(NewSessionSG.input_tournament_name)
        await cb.message.edit_text("Введи название турнира (например: GG Masters $25):")
    else:
        await state.set_state(NewSessionSG.input_limit)
        await cb.message.edit_text("Укажи лимит/ставки (например, NL25):")
    await cb.answer()

@router.message(NewSessionSG.input_tournament_name)
async def input_t_name(msg: Message, state: FSMContext):
    name = (msg.text or "").strip()
    if not name:
        await msg.answer("Название не должно быть пустым. Введи ещё раз:")
        return
    await state.update_data(tournament_name=name[:150])
    await state.set_state(NewSessionSG.input_buyin_rake)
    await msg.answer("Укажи бай-ин. Можно просто число или с рейком.\nПримеры: 25   или   25+2")

@router.message(NewSessionSG.input_buyin_rake)
async def input_buyin_rake(msg: Message, state: FSMContext):
    raw = (msg.text or "").lower().replace(",", ".").strip()
    try:
        if "+" in raw:
            a, b = raw.split("+",1)
            buyin = float(a)
            rake = float(b)
        else:
            buyin = float(raw)
            rake = 0.0
    except Exception:
        await msg.answer("Не получилось распознать. Примеры: 25   или   25+2. Введи ещё раз:")
        return

    await state.update_data(buyin=buyin, rake=rake)
    # PKO вопрос (MVP: просто флаг)
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    kb.button(text="Yes", callback_data="pko:yes")
    kb.button(text="No", callback_data="pko:no")
    await state.set_state(NewSessionSG.choose_pko)
    await msg.answer("Это PKO-турнир?", reply_markup=kb.as_markup())

@router.callback_query(NewSessionSG.choose_pko)
async def choose_pko(cb: CallbackQuery, state: FSMContext):
    is_pko = cb.data == "pko:yes"
    await state.update_data(is_pko=is_pko)

    from ..services import create_session, add_tx, get_or_create_user
    from ..enums import TxType, GameVariant
    async with AsyncSessionLocal() as session:
        data = await state.get_data()
        user = await get_or_create_user(session, cb.from_user.id, cb.from_user.username)
        s = await create_session(
            session,
            user_id=user.id,
            bankroll_id=data["bankroll_id"],
            venue_type=data["venue"],
            format=data["format"],
            game_variant=(data["game"] if isinstance(data.get("game"), GameVariant) else GameVariant[data["game"]]),
            game_name=data.get("game_name"),
            room_id=data.get("room_id"),
            place_id=data.get("place_id"),
            currency=data["currency"],
            tournament_name=data.get("tournament_name"),
            buy_in_amount=data.get("buyin"),
            rake_amount=data.get("rake"),
            is_pko=is_pko,
        )
        # Сразу пишем расходы: BUYIN (+RAKE как EXPENSE)
        await add_tx(session, user_id=user.id, bankroll_id=data["bankroll_id"], session_id=s.id, tx_type=TxType.BUYIN, amount=float(data.get("buyin",0.0)), currency=data["currency"])
        if float(data.get("rake",0.0)) > 0:
            await add_tx(session, user_id=user.id, bankroll_id=data["bankroll_id"], session_id=s.id, tx_type=TxType.EXPENSE, amount=float(data.get("rake",0.0)), currency=data["currency"], note="Rake")

    await state.clear()
    await cb.message.edit_text(
        f"Записал: {data.get('tournament_name')} • Buy-in {data['currency']} {data.get('buyin')}"
        + (f" (+{data['rake']} рейк)" if float(data.get('rake',0))>0 else "")
        + f"\nВозвращаю в меню.",
        reply_markup=main_menu_kb()
    )
    await cb.answer()

@router.message(NewSessionSG.input_limit)
async def input_limit(msg: Message, state: FSMContext):
    text = (msg.text or "").strip()
    if not text:
        await msg.answer("Укажи лимит/ставки, например: NL25")
        return
    await state.update_data(limit=text[:50])
    await state.set_state(NewSessionSG.input_cash_buyin)
    await msg.answer("Укажи сумму первого Buy-in:")

@router.message(NewSessionSG.input_cash_buyin)
async def input_cash_buyin(msg: Message, state: FSMContext):
    raw = (msg.text or "").lower().replace(",", ".").strip()
    try:
        amount = float(raw)
    except Exception:
        await msg.answer("Не получилось распознать. Введи число, например: 50")
        return
    data = await state.get_data()
    from ..services import create_session, add_tx, get_or_create_user
    from ..enums import GameVariant, TxType
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, msg.from_user.id, msg.from_user.username)
        s = await create_session(
            session,
            user_id=user.id,
            bankroll_id=data["bankroll_id"],
            venue_type=data["venue"],
            format=data["format"],
            game_variant=(data["game"] if isinstance(data.get("game"), GameVariant) else GameVariant[data["game"]]),
            game_name=data.get("game_name"),
            room_id=data.get("room_id"),
            place_id=data.get("place_id"),
            currency=data["currency"],
            limit_text=data.get("limit"),
        )
        await add_tx(session, user_id=user.id, bankroll_id=data["bankroll_id"], session_id=s.id, tx_type=TxType.BUYIN, amount=float(amount), currency=data["currency"], note="Cash buy-in")

    await state.clear()
    await msg.answer(
        f"Записал: Cash {data.get('limit')} • Buy-in {data['currency']} {amount}\nВозвращаю в меню.",
        reply_markup=main_menu_kb()
    )
