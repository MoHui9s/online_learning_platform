"""章节模型（stub — 链A 负责完善字段，此处仅提供 courseware 外键引用）。"""
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column()  # FK→courses.id
    title: Mapped[str] = mapped_column(String(200))
    parent_id: Mapped[int | None] = mapped_column(nullable=True)  # FK→chapters.id, 树形
    sort_order: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
