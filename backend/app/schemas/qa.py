"""智能答疑 / AI 助手 / 统计分析 Pydantic v2 模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ===================== C4: RAG 智能答疑 =====================


class KnowledgeBaseBuildRequest(BaseModel):
    """知识库构建请求。"""
    course_id: int


class QAAskRequest(BaseModel):
    """流式问答请求。"""
    question: str = Field(min_length=1)
    course_id: int | None = None  # 限定某门课的知识库


class QAHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    course_id: int | None = None
    question: str
    answer: str | None = None
    sources: dict | None = None
    created_at: datetime


# ===================== C5: AI 学习助手 =====================


class SimilarQuestionRequest(BaseModel):
    """举一反三请求。"""
    wrong_question_id: int  # 错题本中的题目 id


class SuggestionOut(BaseModel):
    """学习建议。"""
    summary: str  # 总评
    weak_points: list[str] = []  # 薄弱知识点
    suggestions: list[str] = []  # 改进建议


class SimilarQuestionOut(BaseModel):
    """变式题。"""
    stem: str
    options: list[dict] | None = None
    answer: dict
    analysis: str | None = None
    based_on_knowledge_point: str | None = None


# ===================== C6: 学习分析统计 =====================


class CalendarDay(BaseModel):
    """学习日历单日数据。"""
    date: str  # YYYY-MM-DD
    duration_minutes: int = 0
    courseware_count: int = 0
    note_count: int = 0


class DurationTrend(BaseModel):
    """学习时长趋势。"""
    period: str  # 日期或周标识
    total_minutes: int = 0


class KnowledgeMastery(BaseModel):
    """知识点掌握度。"""
    knowledge_point_id: int
    knowledge_point_name: str
    total_questions: int = 0
    wrong_count: int = 0
    mastery_rate: float = 0.0  # 正确率百分比


class ExamScoreDistribution(BaseModel):
    """成绩分布。"""
    range_label: str  # "0-59" / "60-69" 等
    count: int = 0


class ExamStats(BaseModel):
    """考试统计。"""
    exam_title: str
    total_students: int = 0
    submitted_count: int = 0
    avg_score: float = 0.0
    pass_rate: float = 0.0  # ≥及格分比例
    distribution: list[ExamScoreDistribution] = []


class CourseOverview(BaseModel):
    """课程概览（教师视角）。"""
    course_id: int
    course_title: str
    enrolled_count: int = 0
    completion_rate: float = 0.0
    avg_progress: float = 0.0
    total_learning_minutes: int = 0
