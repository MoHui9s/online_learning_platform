"""统一响应体与分页结构（对齐 API 规范）。

响应体: { "code": 200, "data": {...}, "message": "success" }
分页 data: { "items": [], "total": 0, "page": 1, "page_size": 20 }
"""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    data: T | None = None
    message: str = "success"


class PageData(BaseModel, Generic[T]):
    items: list[T] = []
    total: int = 0
    page: int = 1
    page_size: int = 20


def success(data=None, message: str = "success", code: int = 200) -> dict:
    """构造统一成功响应（供路由直接 return）。"""
    return {"code": code, "data": data, "message": message}


def paginate(items: list, total: int, page: int, page_size: int) -> dict:
    return {"items": items, "total": total, "page": page, "page_size": page_size}
