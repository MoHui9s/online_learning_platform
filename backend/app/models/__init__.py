"""ORM 模型聚合。新增模型请在此导入，确保 Alembic autogenerate 能发现。"""
from app.models.user import User

# BE-A 模型（stub，BE-A 后续补全字段）
from app.models.course import Course, CourseStatus
from app.models.chapter import Chapter
from app.models.courseware import Courseware, CoursewareType

# BE-B 模型
from app.models.enrollment import Enrollment, EnrollmentStatus
from app.models.learning_record import LearningRecord
from app.models.learning_calendar import LearningCalendar
from app.models.note import Note
from app.models.favorite import Favorite, FavoriteTargetType

# BE-C 模型
from app.models.knowledge_point import KnowledgePoint
from app.models.question import Question, QuestionKnowledgePoint, QuestionType
from app.models.exam import (
    Exam, ExamStatus, ExamQuestion, ExamRecord, ExamRecordStatus, WrongQuestion,
)
from app.models.qa_history import QAHistory

__all__ = [
    # BE-A
    "User",
    "Course",
    "CourseStatus",
    "Chapter",
    "Courseware",
    "CoursewareType",
    # BE-B
    "Enrollment",
    "EnrollmentStatus",
    "LearningRecord",
    "LearningCalendar",
    "Note",
    "Favorite",
    "FavoriteTargetType",
    # BE-C
    "KnowledgePoint",
    "Question",
    "QuestionType",
    "QuestionKnowledgePoint",
    "Exam",
    "ExamStatus",
    "ExamQuestion",
    "ExamRecord",
    "ExamRecordStatus",
    "WrongQuestion",
    "QAHistory",
]
