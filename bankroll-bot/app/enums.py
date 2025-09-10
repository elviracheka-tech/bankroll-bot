from enum import StrEnum

class VenueType(StrEnum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"

class FormatType(StrEnum):
    CASH = "CASH"
    MTT = "MTT"

class GameVariant(StrEnum):
    HOLDEM = "HOLDEM"
    OMAHA = "OMAHA"
    CHOICE = "CHOICE"
    OTHER = "OTHER"

class SessionStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"

class TxType(StrEnum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    EXPENSE = "EXPENSE"
    BONUS = "BONUS"
    RAKEBACK = "RAKEBACK"
    ADJUST = "ADJUST"
    BUYIN = "BUYIN"
    REBUY = "REBUY"
    ADDON = "ADDON"
    CASHOUT = "CASHOUT"
    PRIZE = "PRIZE"
    BOUNTY = "BOUNTY"
    WIN = "WIN"   # итоговое сведение (необяз.)
    LOSS = "LOSS" # итоговое сведение (необяз.)
