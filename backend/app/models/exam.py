"""考试相关模型：exams / exam_questions / exam_records / wrong_questions。"""
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ExamStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    closed = "closed"


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column()  # FK→courses.id
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column()
    total_score: Mapped[int] = mapped_column(default=100)
    pass_score: Mapped[int] = mapped_column(default=60)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[ExamStatus] = mapped_column(Enum(ExamStatus), default=ExamStatus.draft)
    created_by: Mapped[int] = mapped_column()  # FK→users.id
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class ExamQuestion(Base):
    """考试↔题目 多对多关联，带本卷分值 + 题序。"""

    __tablename__ = "exam_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    exam_id: Mapped[int] = mapped_column()  # FK→exams.id
    question_id: Mapped[int] = mapped_column()  # FK→questions.id
    score: Mapped[int] = mapped_column()  # 该题在本卷分值
    sort_order: Mapped[int] = mapped_column(default=0)


class ExamRecordStatus(str, enum.Enum):
    in_progress = "in_progress"
    submitted = "submitted"
    graded = "graded"


class ExamRecord(Base):
    __tablename__ = "exam_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    exam_id: Mapped[int] = mapped_column()  # FK→exams.id
    user_id: Mapped[int] = mapped_column()  # FK→users.id
    answers: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {"question_id": answer}
    score: Mapped[float | None] = mapped_column(nullable=True)
    status: Mapped[ExamRecordStatus] = mapped_column(
        Enum(ExamRecordStatus), default=ExamRecordStatus.in_progress
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class WrongQuestion(Base):
    __tablename__ = "wrong_questions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column()  # FK→users.id
    question_id: Mapped[int] = mapped_column()  # FK→questions.id
    exam_record_id: Mapped[int | None] = mapped_column(nullable=True)  # FK→exam_records.id
    wrong_answer: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    wrong_count: Mapped[int] = mapped_column(default=1)
    is_mastered: Mapped[bool] = mapped_column(default=False)
    last_wrong_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
