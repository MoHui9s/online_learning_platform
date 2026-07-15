"""ORM 模型聚合。新增模型请在此导入，确保 Alembic autogenerate 能发现。"""
from app.models.category import Category
from app.models.chapter import Chapter
from app.models.course import Course
from app.models.courseware import Courseware
from app.models.user import User

__all__ = ["User", "Category", "Course", "Chapter", "Courseware"]
