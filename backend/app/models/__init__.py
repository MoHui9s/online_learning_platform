"""ORM 模型聚合。新增模型请在此导入，确保 Alembic autogenerate 能发现。"""
from app.models.user import User
# 新增以下导入（假设 course 相关模型已存在，一并导出）
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.learning_record import LearningRecord
from app.models.learning_calendar import LearningCalendar
from app.models.note import Note
from app.models.favorite import Favorite, FavoriteTargetType

# 假设已存在的 Course / Courseware / Chapter 模型，如果未创建需要您补齐
# from app.models.course import Course, Courseware, Chapter

__all__ = [
    "User",
    "Enrollment",
    "EnrollmentStatus",
    "LearningRecord",
    "LearningCalendar",
    "Note",
    "Favorite",
    "FavoriteTargetType",
    # "Course", "Courseware", "Chapter",  # 取消注释当实际存在时
]