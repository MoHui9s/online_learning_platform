"""章节模型（对应 docs/database-schema.md 的 chapters 表，树形自关联）。"""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("courses.id"), nullable=False, index=True
    )
    parent_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("chapters.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # 自关联
    parent: Mapped[Optional["Chapter"]] = relationship(
        "Chapter", remote_side="Chapter.id", back_populates="children"
    )
    children: Mapped[list["Chapter"]] = relationship(
        "Chapter", back_populates="parent", order_by="Chapter.sort_order"
    )

    # 关系
    course: Mapped["Course"] = relationship("Course", back_populates="chapters")
    coursewares: Mapped[list["Courseware"]] = relationship(
        "Courseware", back_populates="chapter", order_by="Courseware.sort_order"
    )
