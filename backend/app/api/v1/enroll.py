"""选课模块路由（选课、退课、我的课程列表）。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import success, paginate
from app.schemas.learning import EnrollActionResponse, MyCourseItem
from app.services.enrollment import EnrollmentService

router = APIRouter(tags=["enroll"])

@router.post("/courses/{course_id}/enroll")
def enroll_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """选课接口（幂等复用 dropped 记录）。"""
    try:
        enrollment = EnrollmentService.enroll(db, current_user.id, course_id)
        db.commit()
        return success(
            data=EnrollActionResponse(
                course_id=enrollment.course_id,
                status=enrollment.status,
                enrolled_at=enrollment.enrolled_at,
                message="选课成功",
            ).model_dump(),
            message="选课成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/courses/{course_id}/enroll")
def drop_course(
    course_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """退课接口（置 status = dropped）。"""
    try:
        enrollment = EnrollmentService.drop(db, current_user.id, course_id)
        db.commit()
        return success(
            data=EnrollActionResponse(
                course_id=enrollment.course_id,
                status=enrollment.status,
                enrolled_at=None,
                message="退课成功",
            ).model_dump(),
            message="退课成功"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my/courses")
def get_my_courses(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我的课程列表（分页，含整体进度 progress_percent）。"""
    items, total = EnrollmentService.get_my_courses(
        db, current_user.id, page, page_size
    )
    return success(
        data=paginate(items, total, page, page_size),
        message="获取成功"
    )