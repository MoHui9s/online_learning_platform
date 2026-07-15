"""智能问答历史模型（qa_history 表）。"""
from datetime import datetime

from sqlalchemy import DateTime, JSON, Text, func
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class QAHistory(Base):
    __tablename__ = "qa_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column()  # FK→users.id
    course_id: Mapped[int | None] = mapped_column(nullable=True)  # FK→courses.id
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(MEDIUMTEXT, nullable=True)
    sources: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # RAG 引用
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
