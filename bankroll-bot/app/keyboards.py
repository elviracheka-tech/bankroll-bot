from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .utils import ROOMS, CURRENCIES


def main_menu_kb(has_active_mtt: bool = True) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🆕 New Session", callback_data="menu:new_session")
    if has_active_mtt:
        kb.button(text="🔄 + Rebuy", callback_data="menu:rebuy")
        kb.button(text="🧩 + Addon", callback_data="menu:addon")
    kb.button(text="🏁 Cashout / Finish", callback_data="menu:finish")
    kb.button(text="💰 Balance", callback_data="menu:balance")
    kb.button(text="📜 History", callback_data="menu:history")
    kb.button(text="📊 Report", callback_data="menu:report")
    kb.button(text="⚙️ Settings", callback_data="menu:settings")
    kb.adjust(2, 2, 2, 1)
    return kb.as_markup()


def venue_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="🌐 Online", callback_data="venue:ONLINE")
    kb.button(text="🏠 Offline", callback_data="venue:OFFLINE")
    kb.button(text="✖️ Cancel", callback_data="cancel")
    kb.adjust(2, 1)
    return kb.as_markup()


def format_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="💵 Cash", callback_data="format:CASH")
    kb.button(text="🏆 MTT", callback_data="format:MTT")
    kb.button(text="⬅️ Back", callback_data="back")
    kb.button(text="✖️ Cancel", callback_data="cancel")
    kb.adjust(2, 2)
    return kb.as_markup()


def game_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.button(text="♥️ Holdem", callback_data="game:HOLDEM")
    kb.button(text="♠️ Omaha", callback_data="game:OMAHA")
    kb.button(text="♦️ Choice (Mixed)", callback_data="game:CHOICE")
    kb.button(text="➕ Other", callback_data="game:OTHER")
    kb.button(text="⬅️ Back", callback_data="back")
    kb.button(text="✖️ Cancel", callback_data="cancel")
    kb.adjust(2, 2, 2)
    return kb.as_markup()


def rooms_kb(include_other: bool = True) -> InlineKeyboardMarkup:
    """
    Румы — один столбец (по одной кнопке в строке),
    внизу отдельной строкой — Back и Cancel.
    """
    kb = InlineKeyboardBuilder()

    # по одному в строке
    for text, value in ROOMS:
        kb.row(InlineKeyboardButton(text=text, callback_data=f"room:{value}"))

    if include_other:
        kb.row(InlineKeyboardButton(text="➕ Other", callback_data="room:__OTHER__"))

    # нижняя строка: назад / отмена
    kb.row(
        InlineKeyboardButton(text="⬅️ Back", callback_data="back"),
        InlineKeyboardButton(text="✖️ Cancel", callback_data="cancel"),
    )

    return kb.as_markup()


def currencies_kb() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for text, code in CURRENCIES:
        kb.button(text=text, callback_data=f"cur:{code}")
    kb.button(text="➕ Other", callback_data="cur:__OTHER__")
    kb.button(text="⬅️ Back", callback_data="back")
    kb.button(text="✖️ Cancel", callback_data="cancel")
    kb.adjust(3, 3, 2)
    return kb.as_markup()


def active_sessions_kb(sessions: list[tuple[int, str]]) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    for sid, title in sessions:
        kb.button(text=title, callback_data=f"as:{sid}")
    kb.button(text="⬅️ Back", callback_data="back")
    kb.button(text="✖️ Cancel", callback_data="cancel")
    kb.adjust(1, 2)
    return kb.as_markup()
