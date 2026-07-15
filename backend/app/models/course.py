"""课程模型（对应 docs/database-schema.md 的 courses 表）。"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CourseStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    offline = "offline"


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("categories.id"), nullable=True, index=True
    )
    teacher_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[CourseStatus] = mapped_column(
        Enum(CourseStatus), default=CourseStatus.draft, index=True
    )
    price: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00)
    student_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # 关系
    category: Mapped["Category | None"] = relationship(
        "Category", back_populates="courses"
    )
    teacher: Mapped["User"] = relationship("User")
    chapters: Mapped[list["Chapter"]] = relationship(
        "Chapter", back_populates="course", order_by="Chapter.sort_order"
    )
