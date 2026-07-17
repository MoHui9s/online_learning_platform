"""考试系统 Pydantic v2 模型：知识点 / 题库 / 考试 / 作答 / 错题本。"""

from datetime import datetime

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.exam import ExamRecordStatus, ExamStatus
from app.models.question import QuestionType


def _validate_answer(type, options, answer):
    """校验 answer 结构必须匹配题型。"""
    if type is None or answer is None:
        return
    if type == "short_answer":
        if "text" not in answer:
            raise ValueError("简答题答案须包含 text 字段")
        return
    keys = answer.get("keys", [])
    if not isinstance(keys, list) or not keys:
        raise ValueError(f"{type} 答案须包含 keys")
    if type == "judge":
        option_keys = {"A", "B"}
    else:
        option_keys = {o["key"] for o in (options or [])}
    if not option_keys:
        return
    if type in ("single", "judge"):
        if len(keys) != 1 or keys[0] not in option_keys:
            raise ValueError(f"{type} 答案须为选项中的单个 key")
    elif type == "multiple":
        if not set(keys).issubset(option_keys):
            raise ValueError("多选答案 keys 须为选项 key 的子集")


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

    @model_validator(mode="after")
    def _check_answer(self) -> Self:
        _validate_answer(self.type, self.options, self.answer)
        return self


class QuestionUpdate(BaseModel):
    type: QuestionType | None = None
    stem: str | None = Field(default=None, min_length=1)
    options: list[dict] | None = None
    answer: dict | None = None
    analysis: str | None = None
    difficulty: int | None = Field(default=None, ge=1, le=5)
    score: int | None = Field(default=None, ge=1)
    knowledge_point_ids: list[int] | None = None

    @model_validator(mode="after")
    def _check_answer(self) -> Self:
        _validate_answer(self.type, self.options, self.answer)
        return self


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
