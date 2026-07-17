"""课程分类 Schema。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    parent_id: int | None = None
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    parent_id: int | None = None
    sort_order: int | None = None


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None = None
    sort_order: int
    created_at: datetime
    # 不默认展开 children，由分类树接口按需返回
    children: list["CategoryOut"] | None = None
