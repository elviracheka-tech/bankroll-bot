from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import AsyncSessionLocal
from ..services import get_or_create_user, set_user_nickname
from ..states import RegistrationSG
from ..keyboards import main_menu_kb

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        if not user.nickname:
            await state.set_state(RegistrationSG.waiting_nickname)
            await message.answer("Привет! 👋\nВведи имя или никнейм, который я буду использовать:")
            return
        await message.answer(f"Привет, {user.nickname or 'друг'}! 👋\nЧто делаем?", reply_markup=main_menu_kb())

@router.message(RegistrationSG.waiting_nickname)
async def set_nick(message: Message, state: FSMContext):
    nickname = (message.text or "").strip()
    if not nickname or len(nickname) > 50:
        await message.answer("Пожалуйста, введи имя/никнейм до 50 символов.")
        return
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.username)
        await set_user_nickname(session, user, nickname)
    await state.clear()
    await message.answer(f"Отлично, {nickname}! Теперь можем начать вести банкролл 💰\nЧто делаем?", reply_markup=main_menu_kb())
