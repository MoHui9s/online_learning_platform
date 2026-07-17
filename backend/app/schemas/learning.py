"""学习模块相关 Pydantic 模型（选课、进度）。"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enrollment import EnrollmentStatus


# ---------- 选课 ----------
class EnrollRequest(BaseModel):
    """选课请求体（POST /courses/{id}/enroll）。
    路径参数已包含 course_id，无需额外字段。
    """
    pass


class EnrollResponse(BaseModel):
    """选课/退课成功后返回的简要信息。"""
    course_id: int
    status: EnrollmentStatus
    enrolled_at: datetime


# ---------- 我的课程列表 ----------
class MyCourseItem(BaseModel):
    """我的课程列表中的单条记录（含整体进度）。"""
    model_config = ConfigDict(from_attributes=True)

    # 课程信息（从 courses 表关联）
    course_id: int
    course_title: str
    cover_url: Optional[str] = None
    teacher_name: Optional[str] = None  # 从 users 表关联查询

    # 选课信息（从 enrollments 表）
    status: EnrollmentStatus
    progress_percent: float = Field(description="课程整体进度 (0-100)", ge=0, le=100)
    enrolled_at: datetime


# ---------- 进度上报 ----------
class ProgressReportRequest(BaseModel):
    """进度上报请求体（PUT /learning-records）。"""
    courseware_id: int = Field(..., description="课件ID")

    # 视频课件必传
    last_position: Optional[int] = Field(
        default=0, description="视频断点位置(秒)，非视频传0"
    )
    duration_watched: Optional[int] = Field(
        default=0, description="累计观看时长(秒)，前端维护累计值，后端直接覆盖"
    )

    # 非视频课件必传（由前端根据滚动/翻页自行估算）
    progress_percent: Optional[float] = Field(
        default=None, description="课件进度百分比(0-100)，主要用于文档类课件"
    )


class ProgressReportResponse(BaseModel):
    """进度上报后的返回结果。"""
    courseware_id: int
    progress_percent: float = Field(description="该课件当前进度 (0-100)")
    is_completed: bool = Field(description="是否已达成 95% 完成标记")
    course_progress_percent: float = Field(description="课程整体进度 (0-100)")
    last_position: int = Field(description="更新后的断点位置")


# ---------- 断点获取 ----------
class ResumePointResponse(BaseModel):
    """断点获取响应（GET /courseware/{id}/progress）。"""
    model_config = ConfigDict(from_attributes=True)

    courseware_id: int
    last_position: int = Field(description="上次断点(秒)")
    progress_percent: float = Field(description="该课件进度 (0-100)")
    duration_watched: int = Field(description="累计观看时长(秒)")
    is_completed: bool = Field(description="是否已完成")
    total_duration: Optional[int] = Field(
        default=None, description="课件总时长(秒)，仅视频有值"
    )

class EnrollActionResponse(BaseModel):
    course_id: int
    status: EnrollmentStatus
    enrolled_at: Optional[datetime] = None
    message: str