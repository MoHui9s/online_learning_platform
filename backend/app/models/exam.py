"""考试相关模型：exams / exam_questions / exam_records / wrong_questions。"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ExamStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    closed = "closed"


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    total_score: Mapped[int] = mapped_column(Integer, default=100)
    pass_score: Mapped[int] = mapped_column(Integer, default=60)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[ExamStatus] = mapped_column(
        Enum(ExamStatus), default=ExamStatus.draft, index=True
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class ExamQuestion(Base):
    """考试↔题目 多对多关联，带本卷分值 + 题序。"""
    __tablename__ = "exam_questions"
    __table_args__ = (
        # 唯一约束：一场考试同一题目只出现一次（exam_id 由此前缀覆盖，不建单列索引）
        UniqueConstraint("exam_id", "question_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class ExamRecordStatus(str, enum.Enum):
    in_progress = "in_progress"
    submitted = "submitted"
    graded = "graded"


class ExamRecord(Base):
    __tablename__ = "exam_records"
    __table_args__ = (
        # 复合索引：查某场考试的全部作答/某人是否已作答（exam_id 由此前缀覆盖）
        Index("ix_exam_records_exam_user", "exam_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    answers: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
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
    __table_args__ = (
        # 唯一约束：同一用户同一题只留一条错题记录（user_id 由此前缀覆盖，不建单列索引）
        UniqueConstraint("user_id", "question_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    exam_record_id: Mapped[int | None] = mapped_column(
        ForeignKey("exam_records.id", ondelete="SET NULL"), nullable=True
    )
    wrong_answer: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    wrong_count: Mapped[int] = mapped_column(Integer, default=1)
    is_mastered: Mapped[bool] = mapped_column(default=False)
    last_wrong_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
