"""课程 + 章节 Schema。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.course import CourseStatus
from app.schemas.category import CategoryOut


# ─── 课程 ───────────────────────────────────────────────
class CourseBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    cover_url: str | None = None
    category_id: int | None = None
    price: float = 0.00


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    cover_url: str | None = None
    category_id: int | None = None
    status: CourseStatus | None = None
    price: float | None = None


class CourseStatusRequest(BaseModel):
    """状态流转 — PATCH /courses/{id}/status。"""
    status: CourseStatus


class CourseListItem(BaseModel):
    """列表项（轻量，不含章节树）。"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    cover_url: str | None = None
    category_id: int | None = None
    teacher_id: int
    status: CourseStatus
    price: float
    student_count: int
    created_at: datetime


class CourseOut(BaseModel):
    """详情（含分类信息 + 章节树）。"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    cover_url: str | None = None
    category_id: int | None = None
    category: CategoryOut | None = None
    teacher_id: int
    status: CourseStatus
    price: float
    student_count: int
    created_at: datetime
    chapters: list["ChapterOut"] | None = None


# ─── 章节 ───────────────────────────────────────────────
class ChapterBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    parent_id: int | None = None
    sort_order: int = 0


class ChapterCreate(ChapterBase):
    pass


class ChapterUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: int | None = None
    sort_order: int | None = None


class ChapterSortItem(BaseModel):
    id: int
    sort_order: int


class ChapterSortRequest(BaseModel):
    items: list[ChapterSortItem]


class ChapterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    parent_id: int | None = None
    title: str
    sort_order: int
    created_at: datetime
    children: list["ChapterOut"] | None = None


# ─── 课件 ───────────────────────────────────────────────

class CoursewareCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    type: str = Field(min_length=1, max_length=50)
    sort_order: int = 0


class CoursewareUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    sort_order: int | None = None


class CoursewareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chapter_id: int
    title: str
    type: str
    file_path: str
    file_name: str | None = None
    file_size: int | None = None
    mime_type: str | None = None
    duration: int | None = None
    sort_order: int = 0
    uploaded_by: int | None = None
    created_at: datetime
    updated_at: datetime
