"""学习日历日聚合（对应 database-schema.md 的 learning_calendar 表）。"""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LearningCalendar(Base):
    __tablename__ = "learning_calendar"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    study_date: Mapped[date] = mapped_column(Date, nullable=False)
    duration_seconds: Mapped[int] = mapped_column(default=0)
    courseware_count: Mapped[int] = mapped_column(default=0)
    note_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user = relationship("User", backref="learning_calendars")

    __table_args__ = (
        # 唯一约束：每天每人只有一条聚合记录
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )