"""考试系统 Pydantic v2 模型：知识点 / 题库 / 考试 / 作答 / 错题本。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.exam import ExamRecordStatus, ExamStatus
from app.models.question import QuestionType


# ===================== 知识点 =====================
class KnowledgePointCreate(BaseModel):
    parent_id: int | None = None
    name: str = Field(min_length=1, max_length=128)
    description: str | None = None


class KnowledgePointUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None


class KnowledgePointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    parent_id: int | None = None
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime
    children: list["KnowledgePointOut"] = []  # 树形返回


# ===================== 题库 =====================
class QuestionCreate(BaseModel):
    course_id: int
    type: QuestionType
    stem: str = Field(min_length=1)
    options: list[dict] | None = None  # [{"key":"A","text":"..."}]
    answer: dict  # {"keys": ["A","B"]} 或 {"text": "参考回答"}
    analysis: str | None = None
    difficulty: int = Field(default=3, ge=1, le=5)
    score: int = Field(default=5, ge=1)
    knowledge_point_ids: list[int] = []  # 关联知识点


class QuestionUpdate(BaseModel):
    type: QuestionType | None = None
    stem: str | None = Field(default=None, min_length=1)
    options: list[dict] | None = None
    answer: dict | None = None
    analysis: str | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)
    score: int | None = Field(default=None, ge=1)
    knowledge_point_ids: list[int] | None = None


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    type: QuestionType
    stem: str
    options: list[dict] | None = None
    answer: dict
    analysis: str | None = None
    difficulty: int
    score: int
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime
    knowledge_point_ids: list[int] = []


class QuestionBrief(BaseModel):
    """学生视角：不含答案和解析。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    type: QuestionType
    stem: str
    options: list[dict] | None = None
    difficulty: int
    score: int


# ===================== 考试 =====================
class ExamCreate(BaseModel):
    course_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    duration_minutes: int = Field(ge=1)
    total_score: int = Field(default=100, ge=1)
    pass_score: int = Field(default=60, ge=1)
    start_time: datetime | None = None
    end_time: datetime | None = None


class ExamSetQuestions(BaseModel):
    """组卷：向考试添加题目。"""
    questions: list["ExamQuestionItem"]


class ExamQuestionItem(BaseModel):
    question_id: int
    score: int = Field(ge=1)
    sort_order: int = 0


class ExamUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    duration_minutes: int | None = Field(default=None, ge=1)
    total_score: int | None = Field(default=None, ge=1)
    pass_score: int | None = Field(default=None, ge=1)
    start_time: datetime | None = None
    end_time: datetime | None = None
    questions: list[ExamQuestionItem] | None = None


class ExamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    title: str
    description: str | None = None
    duration_minutes: int
    total_score: int
    pass_score: int
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: ExamStatus
    created_by: int
    created_at: datetime
    updated_at: datetime
    question_count: int = 0  # 题目数量


class ExamDetailOut(ExamOut):
    """教师视角：含题目详情（带答案）。"""
    questions: list[QuestionOut] = []


class ExamPreviewOut(ExamOut):
    """学生视角：仅含题目题干（不含答案）。"""
    questions: list[QuestionBrief] = []


# ===================== 考试作答 =====================
class ExamStartResponse(BaseModel):
    record_id: int
    started_at: datetime
    questions: list[QuestionBrief]


class AnswerSubmit(BaseModel):
    """提交单题答案。"""

    question_id: int
    answer: dict  # 格式取决于题型


class ExamSubmitRequest(BaseModel):
    answers: list[AnswerSubmit]


class ExamRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    exam_id: int
    user_id: int
    answers: dict | None = None
    score: float | None = None
    status: ExamRecordStatus
    started_at: datetime | None = None
    submitted_at: datetime | None = None
    created_at: datetime


class ExamRecordDetailOut(ExamRecordOut):
    """作答详情：含题目 + 正确答案（交卷后可见）。"""
    questions: list[QuestionOut] = []


# ===================== 错题本 =====================
class WrongQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    question_id: int
    exam_record_id: int | None = None
    wrong_answer: dict | None = None
    wrong_count: int
    is_mastered: bool
    last_wrong_at: datetime | None = None
    created_at: datetime
    # 关联题目摘要
    question: QuestionBrief | None = None
