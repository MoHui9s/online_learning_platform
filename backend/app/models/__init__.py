"""ORM 模型聚合。新增模型请在此导入，确保 Alembic autogenerate 能发现。"""
from app.models.user import User
from app.models.course import Course
from app.models.chapter import Chapter
from app.models.courseware import Courseware
from app.models.knowledge_point import KnowledgePoint
from app.models.question import Question, QuestionKnowledgePoint
from app.models.exam import Exam, ExamQuestion, ExamRecord, WrongQuestion
from app.models.qa_history import QAHistory
from app.models.learning import Enrollment, LearningRecord, LearningCalendar

__all__ = [
    "User",
    "Course",
    "Chapter",
    "Courseware",
    "KnowledgePoint",
    "Question",
    "QuestionKnowledgePoint",
    "Exam",
    "ExamQuestion",
    "ExamRecord",
    "WrongQuestion",
    "QAHistory",
    "Enrollment",
    "LearningRecord",
    "LearningCalendar",
]
