from datetime import datetime
from pydantic import BaseModel, ConfigDict


class LearningProgressIn(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_id: int
    chapter_id: int | None = None
    progress: int


class LearningRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    course_id: int
    chapter_id: int | None = None
    course_title: str | None = None
    chapter_title: str | None = None
    progress: int
    created_at: datetime
    updated_at: datetime
