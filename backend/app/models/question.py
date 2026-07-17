"""题目模型（questions 表）+ 题目-知识点关联（question_knowledge_points）。"""
import enum
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, JSON, SmallInteger, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class QuestionType(str, enum.Enum):
    single = "single"
    multiple = "multiple"
    judge = "judge"
    short_answer = "short_answer"


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType), nullable=False, index=True
    )
    stem: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    answer: Mapped[dict] = mapped_column(JSON, nullable=False)
    analysis: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[int] = mapped_column(SmallInteger, default=3)
    score: Mapped[int] = mapped_column(Integer, default=5)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class QuestionKnowledgePoint(Base):
    __tablename__ = "question_knowledge_points"
    __table_args__ = (
        # 唯一约束：同一题目与知识点只关联一次（question_id 由此前缀覆盖，不建单列索引）
        UniqueConstraint("question_id", "knowledge_point_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    knowledge_point_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_points.id", ondelete="CASCADE"), nullable=False, index=True
    )
