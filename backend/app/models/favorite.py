"""收藏模型（多态，对应 database-schema.md 的 favorites 表）。"""
from datetime import datetime
import enum

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class FavoriteTargetType(str, enum.Enum):
    course = "course"
    courseware = "courseware"
    note = "note"


class Favorite(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_type: Mapped[FavoriteTargetType] = mapped_column(
        Enum(FavoriteTargetType), nullable=False
    )
    target_id: Mapped[int] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    user = relationship("User", backref="favorites")

    __table_args__ = (
        # 唯一约束：防重复收藏
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8mb4"},
    )