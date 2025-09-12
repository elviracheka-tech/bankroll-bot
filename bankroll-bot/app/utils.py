from .enums import TxType

# Определяем знак транзакции
INCOME_TYPES = {TxType.CASHOUT, TxType.PRIZE, TxType.BOUNTY, TxType.BONUS, TxType.RAKEBACK, TxType.WIN}
EXPENSE_TYPES = {TxType.BUYIN, TxType.REBUY, TxType.ADDON, TxType.EXPENSE, TxType.WITHDRAW, TxType.LOSS, TxType.ADJUST}

def signed_amount(tx_type: TxType, amount: float) -> float:
    if tx_type in INCOME_TYPES:
        return float(amount)
    return -float(amount)

ROOMS = [
    ("👌 PokerOK (GG)", "PokerOK (GG)"),
    ("⭐ PokerStars", "PokerStars"),
    ("🇷🇺 PokerDom", "PokerDom"),
    ("🎱 888poker", "888poker"),
    ("🎉 PartyPoker", "PartyPoker"),
    ("👑 PokerKing (WPN)", "PokerKing (WPN)"),
    ("🔴 RedStar (iPoker)", "RedStar (iPoker)"),
    ("🐯 TigerGaming", "TigerGaming"),
    ("🇫🇷 Winamax", "Winamax"),
]

CURRENCIES = [
    ("💵 USD", "USD"),
    ("💶 EUR", "EUR"),
    ("🇷🇺 RUB", "RUB"),
]
