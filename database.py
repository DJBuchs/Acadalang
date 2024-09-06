from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean, Float, DateTime, ForeignKey, Date
from flask_login import UserMixin
from datetime import datetime, timedelta
from typing import List


class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(18), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)


class Card(db.Model):
    __tablename__ = "flashcards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    english: Mapped[str] = mapped_column(String(50), nullable=False)
    hebrew: Mapped[str] = mapped_column(String(100), nullable=False)
    seen: Mapped[bool] = mapped_column(Boolean, default=False)
    next_shown: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # Fields for spaced repetition
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)  # Easiness factor (EF)
    interval: Mapped[int] = mapped_column(Integer, default=0)  # Interval in days

    # relationship mapping for cash game
    deck_id: Mapped[int] = mapped_column(ForeignKey("decks.id", ondelete="CASCADE"))
    deck: Mapped["Deck"] = relationship("Deck", back_populates="card_data")

    def __repr__(self):
        return (f"<Card(id={self.id}, english='{self.english}', hebrew='{self.hebrew}', "
                f"seen={self.seen}, next_shown={self.next_shown}, easiness={self.ease_factor}, "
                f"interval={self.interval})>")
    

class Deck(db.Model):
    __tablename__ = "decks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    num_cards: Mapped[int] = mapped_column(Integer, nullable=False)
    streak: Mapped[int] = mapped_column(Integer, default=0)
    unseen_count: Mapped[int] = mapped_column(Integer, default=0)
    date: Mapped[datetime] = mapped_column(Date, default=(datetime.now() - timedelta(days=1)).date())

    # relationship mapping for game sessions
    card_data: Mapped[List["Card"]] = relationship("Card", back_populates="deck", cascade="all, delete-orphan")



