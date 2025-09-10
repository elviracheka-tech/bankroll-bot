from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, BigInteger, DateTime, ForeignKey, Boolean, Numeric, Enum, Text
from .db import Base
from .enums import VenueType, FormatType, GameVariant, SessionStatus, TxType

NUMERIC_ = Numeric(12, 2)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    tg_username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    nickname: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bankrolls = relationship("Bankroll", back_populates="user")

class Bankroll(Base):
    __tablename__ = "bankrolls"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    currency: Mapped[str] = mapped_column(String(10))  # USD/EUR/RUB
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="bankrolls")

class UserRoom(Base):
    __tablename__ = "user_rooms"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    default_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

class UserPlace(Base):
    __tablename__ = "user_places"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(100))
    default_currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    bankroll_id: Mapped[int] = mapped_column(ForeignKey("bankrolls.id", ondelete="RESTRICT"))

    venue_type: Mapped[VenueType] = mapped_column(Enum(VenueType))
    format: Mapped[FormatType] = mapped_column(Enum(FormatType))
    game_variant: Mapped[GameVariant] = mapped_column(Enum(GameVariant))
    game_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    room_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_rooms.id"), nullable=True)
    place_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_places.id"), nullable=True)
    currency: Mapped[str] = mapped_column(String(10))

    tournament_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    buy_in_amount: Mapped[Optional[float]] = mapped_column(NUMERIC_, nullable=True)
    rake_amount: Mapped[Optional[float]] = mapped_column(NUMERIC_, nullable=True)
    is_pko: Mapped[bool] = mapped_column(Boolean, default=False)

    rebuy_count: Mapped[int] = mapped_column(Integer, default=0)
    addon_count: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Cash-only fields
    limit_text: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Close stats (optional view)
    payout_amount: Mapped[Optional[float]] = mapped_column(NUMERIC_, nullable=True)
    bounty_amount: Mapped[Optional[float]] = mapped_column(NUMERIC_, nullable=True)
    finish_place: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    bankroll_id: Mapped[int] = mapped_column(ForeignKey("bankrolls.id", ondelete="RESTRICT"), index=True)
    session_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sessions.id", ondelete="CASCADE"), nullable=True)

    type: Mapped[TxType] = mapped_column(Enum(TxType))
    amount: Mapped[float] = mapped_column(NUMERIC_)  # хранится положительным числом
    currency: Mapped[str] = mapped_column(String(10))

    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
