"""课件 Schema。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.courseware import CoursewareType


class CoursewareCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    type: CoursewareType
    sort_order: int = 0


class CoursewareUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    sort_order: int | None = None


class CoursewareOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chapter_id: int
    title: str
    type: CoursewareType
    file_path: str
    file_name: str | None = None
    file_size: int | None = None
    mime_type: str | None = None
    duration: int | None = None
    sort_order: int
    uploaded_by: int | None = None
    created_at: datetime
