from datetime import datetime
from typing import Optional, Sequence
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User, Bankroll, UserRoom, UserPlace, Session, Transaction
from .enums import VenueType, FormatType, GameVariant, SessionStatus, TxType
from .utils import signed_amount

# --- Users ---
async def get_or_create_user(db: AsyncSession, telegram_id: int, tg_username: Optional[str]) -> User:
    res = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = res.scalar_one_or_none()
    if user:
        return user
    user = User(telegram_id=telegram_id, tg_username=tg_username)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def set_user_nickname(db: AsyncSession, user: User, nickname: str) -> None:
    user.nickname = nickname.strip()[:50]
    await db.commit()

# --- Bankrolls ---
async def list_bankrolls(db: AsyncSession, user_id: int, currency: Optional[str] = None) -> Sequence[Bankroll]:
    q = select(Bankroll).where(Bankroll.user_id == user_id)
    if currency:
        q = q.where(Bankroll.currency == currency)
    q = q.order_by(Bankroll.is_default.desc(), Bankroll.id.asc())
    res = await db.execute(q)
    return res.scalars().all()

async def create_bankroll(db: AsyncSession, user_id: int, name: str, currency: str, make_default: bool = True) -> Bankroll:
    if make_default:
        await db.execute(update(Bankroll).where(Bankroll.user_id == user_id).values(is_default=False))
    br = Bankroll(user_id=user_id, name=name, currency=currency, is_default=make_default)
    db.add(br)
    await db.commit()
    await db.refresh(br)
    return br

# --- Rooms/Places currency defaults ---
async def get_or_create_room(db: AsyncSession, user_id: int, name: str) -> UserRoom:
    res = await db.execute(select(UserRoom).where(UserRoom.user_id == user_id, UserRoom.name == name))
    room = res.scalar_one_or_none()
    if room:
        return room
    room = UserRoom(user_id=user_id, name=name)
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room

async def get_or_create_place(db: AsyncSession, user_id: int, name: str) -> UserPlace:
    res = await db.execute(select(UserPlace).where(UserPlace.user_id == user_id, UserPlace.name == name))
    place = res.scalar_one_or_none()
    if place:
        return place
    place = UserPlace(user_id=user_id, name=name)
    db.add(place)
    await db.commit()
    await db.refresh(place)
    return place

# --- Sessions ---
async def create_session(
    db: AsyncSession,
    *,
    user_id: int,
    bankroll_id: int,
    venue_type: VenueType,
    format: FormatType,
    game_variant: GameVariant,
    game_name: Optional[str],
    room_id: Optional[int],
    place_id: Optional[int],
    currency: str,
    tournament_name: Optional[str] = None,
    limit_text: Optional[str] = None,
    buy_in_amount: Optional[float] = None,
    rake_amount: Optional[float] = None,
    is_pko: bool = False,
) -> Session:
    s = Session(
        user_id=user_id,
        bankroll_id=bankroll_id,
        venue_type=venue_type,
        format=format,
        game_variant=game_variant,
        game_name=game_name,
        room_id=room_id,
        place_id=place_id,
        currency=currency,
        tournament_name=tournament_name,
        limit_text=limit_text,
        buy_in_amount=buy_in_amount,
        rake_amount=rake_amount,
        is_pko=is_pko,
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    return s

async def add_tx(db: AsyncSession, *, user_id: int, bankroll_id: int, session_id: Optional[int], tx_type: TxType, amount: float, currency: str, note: str | None = None) -> Transaction:
    tx = Transaction(user_id=user_id, bankroll_id=bankroll_id, session_id=session_id, type=tx_type, amount=amount, currency=currency, note=note)
    db.add(tx)
    await db.commit()
    await db.refresh(tx)
    return tx

async def list_active_sessions(db: AsyncSession, user_id: int) -> list[Session]:
    res = await db.execute(select(Session).where(Session.user_id == user_id, Session.status == SessionStatus.ACTIVE).order_by(Session.started_at.asc()))
    return list(res.scalars().all())

async def close_session(db: AsyncSession, session: Session) -> None:
    session.status = SessionStatus.CLOSED
    session.ended_at = datetime.utcnow()
    await db.commit()

# --- Balance & Reports ---
async def bankroll_balance(db: AsyncSession, user_id: int, bankroll_id: int) -> float:
    res = await db.execute(select(Transaction.type, func.sum(Transaction.amount)).where(Transaction.user_id == user_id, Transaction.bankroll_id == bankroll_id, Transaction.is_deleted == False).group_by(Transaction.type))
    total = 0.0
    for tx_type, sum_amount in res.all():
        # sum_amount may be Decimal
        total += signed_amount(tx_type, float(sum_amount or 0))
    return round(total, 2)

async def report_stats(db: AsyncSession, user_id: int, currency: str, date_from: datetime, date_to: datetime) -> dict:
    # Суммарный профит как сумма sign(amount) по всем транзакциям данной валюты
    res = await db.execute(select(Transaction.type, func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id,
        Transaction.currency == currency,
        Transaction.at >= date_from,
        Transaction.at < date_to,
        Transaction.is_deleted == False,
    ).group_by(Transaction.type))
    profit = 0.0
    for tx_type, s in res.all():
        profit += signed_amount(tx_type, float(s or 0.0))

    # Кол-во закрытых сессий в периоде
    sres = await db.execute(select(func.count()).select_from(Session).where(
        Session.user_id == user_id,
        Session.currency == currency,
        Session.status == SessionStatus.CLOSED,
        Session.ended_at != None,
        Session.ended_at >= date_from,
        Session.ended_at < date_to,
    )))
    sessions_count = int(sres.scalar() or 0)

    avg_per_session = round(profit / sessions_count, 2) if sessions_count else 0.0

    return {
        "profit": round(profit, 2),
        "sessions": sessions_count,
        "avg_per_session": avg_per_session,
    }
