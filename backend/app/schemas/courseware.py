"""课件 Pydantic v2 模型。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.courseware import CoursewareType


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
    updated_at: datetime
