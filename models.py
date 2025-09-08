from sqlalchemy import Integer, String, BigInteger, DateTime, Enum, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import List
from enum import Enum as PyEnum

from db import Base


class RecurrenceEnum(PyEnum):
    ONCE = 'once'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'


class StatutEnum(PyEnum):
    ACTIVE = 'active'
    DELETED = 'deleted'
    COMPLETED = 'completed'


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), index=True, unique=True, nullable=False)

    events: Mapped[List['Event']] = relationship(back_populates='user', cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = 'events'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    event_datetime: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    custom_reminder: Mapped[int] = mapped_column(Integer, default=0)
    recurrence: Mapped[RecurrenceEnum] = mapped_column(Enum(RecurrenceEnum), default=RecurrenceEnum.ONCE)
    status: Mapped[StatutEnum] = mapped_column(Enum(StatutEnum), default=StatutEnum.ACTIVE, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)

    user: Mapped['User'] = relationship(back_populates='events')