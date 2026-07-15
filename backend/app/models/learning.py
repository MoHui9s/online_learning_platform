"""BE-B 表 Stub（C6 统计模块依赖的读端表）。"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Enrollment(Base):
    """选课关系 stub（BE-B 负责完善）。"""
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column()
    course_id: Mapped[int] = mapped_column()
    progress_percent: Mapped[float] = mapped_column(default=0.0)  # 整体进度
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class LearningRecord(Base):
    """学习进度 stub（BE-B 负责完善）。"""
    __tablename__ = "learning_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column()
    course_id: Mapped[int] = mapped_column()
    courseware_id: Mapped[int] = mapped_column()
    last_position: Mapped[int] = mapped_column(default=0)
    duration_watched: Mapped[int] = mapped_column(default=0)  # 累计观看时长(秒)
    is_completed: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class LearningCalendar(Base):
    """学习日历 stub（BE-B 负责完善）。"""
    __tablename__ = "learning_calendar"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column()
    study_date: Mapped[date] = mapped_column(Date)
    duration_seconds: Mapped[int] = mapped_column(default=0)
    courseware_count: Mapped[int] = mapped_column(default=0)
    note_count: Mapped[int] = mapped_column(default=0)
