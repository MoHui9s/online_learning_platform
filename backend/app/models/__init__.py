"""ORM 模型聚合。新增模型请在此导入，确保 Alembic autogenerate 能发现。"""
from app.models.user import User

__all__ = ["User"]
