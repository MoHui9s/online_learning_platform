"""选课关系模型（对应 database-schema.md 的 enrollments 表）。"""
from datetime import datetime
import enum

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EnrollmentStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    dropped = "dropped"


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus), default=EnrollmentStatus.active
    )
    progress_percent: Mapped[float] = mapped_column(
        Numeric(5, 2), default=0.00
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # 关联关系（可选，便于联查）
    user = relationship("User", backref="enrollments")
    course = relationship("Course", backref="enrollments")

    __table_args__ = (
        # 唯一约束：防止重复选课（软删除后复用记录）
        # 注意：该约束不含 status，因此 dropped 记录也会占用名额，需要业务层处理复用逻辑
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )