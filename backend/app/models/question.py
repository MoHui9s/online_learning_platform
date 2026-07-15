"""题目模型（questions 表）+ 题目-知识点关联（question_knowledge_points）。"""
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, JSON, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class QuestionType(str, enum.Enum):
    single = "single"
    multiple = "multiple"
    judge = "judge"
    short_answer = "short_answer"


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column()  # FK→courses.id
    type: Mapped[QuestionType] = mapped_column(Enum(QuestionType))
    stem: Mapped[str] = mapped_column(Text)  # 题干
    options: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # [{"key":"A","text":"..."}]
    answer: Mapped[dict] = mapped_column(JSON)  # 客观题为 key 数组，简答为参考文本
    analysis: Mapped[str | None] = mapped_column(Text, nullable=True)  # 解析
    difficulty: Mapped[int] = mapped_column(default=3)  # 1-5
    score: Mapped[int] = mapped_column(default=5)
    created_by: Mapped[int | None] = mapped_column(nullable=True)  # FK→users.id
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class QuestionKnowledgePoint(Base):
    __tablename__ = "question_knowledge_points"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    question_id: Mapped[int] = mapped_column()  # FK→questions.id
    knowledge_point_id: Mapped[int] = mapped_column()  # FK→knowledge_points.id
