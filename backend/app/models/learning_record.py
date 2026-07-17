"""学习进度记录（对应 database-schema.md 的 learning_records 表）。"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LearningRecord(Base):
    __tablename__ = "learning_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    courseware_id: Mapped[int] = mapped_column(
        ForeignKey("courseware.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    last_position: Mapped[int] = mapped_column(default=0)  # 视频断点(秒)
    progress_percent: Mapped[float] = mapped_column(
        Numeric(5, 2), default=0.00
    )
    duration_watched: Mapped[int] = mapped_column(default=0)  # 累计观看秒数
    is_completed: Mapped[bool] = mapped_column(default=False)
    last_learned_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # 关联关系
    user = relationship("User", backref="learning_records")
    course = relationship("Course", backref="learning_records")
    courseware = relationship("Courseware", backref="learning_records")

    __table_args__ = (
        # 唯一约束：每个用户对每个课件只能有一条记录
        UniqueConstraint("user_id", "courseware_id"),
        # 复合索引：按用户+课程聚合查询学习进度（user_id 由此前缀覆盖，不建单列索引）
        Index("ix_learning_records_user_course", "user_id", "course_id"),
    )
