"""课程 + 章节路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_teacher
from app.models.user import User
from app.schemas.common import paginate, success
from app.schemas.course import (
    ChapterCreate,
    ChapterOut,
    ChapterSortRequest,
    ChapterUpdate,
    CourseCreate,
    CourseOut,
    CourseStatusRequest,
    CourseUpdate,
)
from app.services import chapter_service, course_service

router = APIRouter(prefix="/courses", tags=["courses"])


# ─── 课程 ───────────────────────────────────────────────
@router.get("")
def list_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: str | None = None,
    category_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    items, total = course_service.get_list(
        db, page, page_size, keyword, category_id, status
    )
    return success(paginate(items, total, page, page_size))


@router.get("/{course_id}")
def course_detail(course_id: int, db: Session = Depends(get_db)):
    course = course_service.get_detail(db, course_id)
    return success(CourseOut.model_validate(course).model_dump())


@router.post("")
def create_course(
    payload: CourseCreate,
    current: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    course = course_service.create_course(db, current, **payload.model_dump())
    return success(
        CourseOut.model_validate(course).model_dump(), message="课程创建成功"
    )


@router.put("/{course_id}")
def update_course(
    course_id: int,
    payload: CourseUpdate,
    current: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    course = course_service.update_course(
        db, course_id, current, payload.model_dump(exclude_none=True)
    )
    return success(CourseOut.model_validate(course).model_dump(), message="课程已更新")


@router.put("/{course_id}/status")
def change_course_status(
    course_id: int,
    payload: CourseStatusRequest,
    current: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """状态流转：draft → published → offline → draft。"""
    course = course_service.change_status(db, course_id, current, payload.status)
    return success(
        CourseOut.model_validate(course).model_dump(),
        message=f"课程状态已变更为 {payload.status.value}",
    )


@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    current: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    course_service.delete_course(db, course_id, current)
    return success(message="课程已删除")


# ─── 章节 ───────────────────────────────────────────────
@router.get("/{course_id}/chapters")
def list_chapters(course_id: int, db: Session = Depends(get_db)):
    """获取课程的章节树。"""
    tree = chapter_service.get_chapters_by_course(db, course_id)
    return success(tree)


@router.post("/{course_id}/chapters")
def create_chapter(
    course_id: int,
    payload: ChapterCreate,
    current: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    ch = chapter_service.create(
        db, course_id, payload.title, payload.parent_id, payload.sort_order
    )
    return success(ChapterOut.model_validate(ch).model_dump(), message="章节创建成功")


@router.put("/{course_id}/chapters/sort")
def sort_chapters(
    course_id: int,
    payload: ChapterSortRequest,
    current: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    """批量调整章节排序。请求体: { "items": [{"id": 1, "sort_order": 0}, ...] }"""
    items = [{"id": item.id, "sort_order": item.sort_order} for item in payload.items]
    chapters = chapter_service.batch_sort(db, course_id, items)
    return success(
        [ChapterOut.model_validate(ch).model_dump() for ch in chapters],
        message="章节排序已更新",
    )


@router.put("/{course_id}/chapters/{chapter_id}")
def update_chapter(
    course_id: int,
    chapter_id: int,
    payload: ChapterUpdate,
    current: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    ch = chapter_service.update(
        db, chapter_id, payload.title, payload.parent_id, payload.sort_order
    )
    return success(ChapterOut.model_validate(ch).model_dump(), message="章节已更新")


@router.delete("/{course_id}/chapters/{chapter_id}")
def delete_chapter(
    course_id: int,
    chapter_id: int,
    current: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    chapter_service.delete(db, chapter_id)
    return success(message="章节已删除")
