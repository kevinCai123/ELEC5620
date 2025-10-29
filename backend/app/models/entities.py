from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    items: Mapped[list["PlanItem"]] = relationship(
        "PlanItem", back_populates="plan", cascade="all, delete-orphan"
    )


class PlanItem(Base):
    __tablename__ = "plan_items"
    __table_args__ = (UniqueConstraint("plan_id", "uid", name="uq_plan_item_uid"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    uid: Mapped[str] = mapped_column(String(255), nullable=False)

    plan: Mapped[Plan] = relationship("Plan", back_populates="items")


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    due_at_confidence: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Quiz(Base):
    __tablename__ = "quizzes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    items_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    attempts: Mapped[list["QuizAttempt"]] = relationship(
        "QuizAttempt", back_populates="quiz", cascade="all, delete-orphan"
    )


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"))
    answers_json: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    quiz: Mapped[Quiz] = relationship("Quiz", back_populates="attempts")


class UserPreference(Base):
    __tablename__ = "user_prefs"

    user_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    digest_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    digest_time: Mapped[str | None] = mapped_column(String(5), nullable=True)
    timezone: Mapped[str] = mapped_column(String(64), default="Australia/Sydney", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class DigestDeliveryLog(Base):
    __tablename__ = "digest_delivery_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    channel: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    query: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
