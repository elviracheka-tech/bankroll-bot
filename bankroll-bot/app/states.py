from aiogram.fsm.state import StatesGroup, State

class RegistrationSG(StatesGroup):
    waiting_nickname = State()

class NewSessionSG(StatesGroup):
    choose_venue = State()
    choose_format = State()
    choose_game = State()
    input_game_name = State()
    choose_room = State()
    input_room_other = State()
    choose_place = State()
    input_place_other = State()
    choose_currency = State()
    choose_bankroll = State()

    # MTT
    input_tournament_name = State()
    input_buyin_rake = State()
    choose_pko = State()

    # CASH
    input_limit = State()
    input_cash_buyin = State()

class RebuyAddonSG(StatesGroup):
    choose_tournament_for_action = State()
    input_amount_override = State()  # reserved

class FinishSG(StatesGroup):
    choose_session = State()
    input_cashout = State()
    ask_pko_split = State()
    input_bounty = State()
    input_prize = State()
    input_total_prize = State()

class ReportSG(StatesGroup):
    choose_currency = State()
    choose_period = State()
    input_custom_from = State()
    input_custom_to = State()

class HistorySG(StatesGroup):
    browsing = State()
    editing = State()
