"""课程 & 章节路由：CRUD + 列表 + 详情 + 拖拽排序。"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.category import Category
from app.models.chapter import Chapter
from app.models.course import Course, CourseStatus
from app.models.courseware import Courseware
from app.models.user import User
from app.schemas.common import paginate, success
from app.schemas.course import (
    CategoryOut,
    ChapterCreate,
    ChapterDetailOut,
    ChapterOut,
    ChapterSortRequest,
    ChapterUpdate,
    CourseCreate,
    CourseListItem,
    CourseOut,
    CourseStatusRequest,
    CourseUpdate,
)

router = APIRouter(prefix="/courses", tags=["courses"])


# ── 课程列表 + 分类 ──────────────────────────────────

@router.get("")
def list_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None, alias="q"),
    status: Optional[CourseStatus] = None,
    category_id: Optional[int] = None,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Course).options(selectinload(Course.category))
    if keyword:
        query = query.where(Course.title.ilike(f"%{keyword}%"))
    if status:
        query = query.where(Course.status == status)
    if category_id:
        query = query.where(Course.category_id == category_id)

    total = db.execute(select(func.count()).select_from(query.subquery())).scalar_one()
    items = (
        db.execute(
            query.order_by(Course.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        .scalars()
        .all()
    )
    payload = []
    for course in items:
        data = CourseListItem.model_validate(course).model_dump()
        data["category_name"] = course.category.name if course.category else None
        payload.append(data)
    return success(paginate(payload, total, page, page_size))


@router.get("/categories")
def list_categories(_: object = Depends(get_current_user), db: Session = Depends(get_db)):
    categories = (
        db.execute(select(Category).order_by(Category.sort_order.asc(), Category.id.asc()))
        .scalars()
        .all()
    )
    return success([CategoryOut.model_validate(category).model_dump() for category in categories])


# ── 课程 CRUD ──────────────────────────────────────

@router.post("", status_code=201)
def create_course(
    payload: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = Course(
        title=payload.title,
        description=payload.description,
        cover_url=payload.cover_url,
        category_id=payload.category_id,
        teacher_id=current_user.id,
        price=payload.price,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return success(CourseOut.model_validate(course).model_dump(), message="课程已创建")


@router.put("/{course_id}")
def update_course(
    course_id: int,
    payload: CourseUpdate,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.execute(
        select(Course).where(Course.id == course_id)
    ).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    updated = False
    if payload.title is not None:
        course.title = payload.title
        updated = True
    if payload.description is not None:
        course.description = payload.description or None
        updated = True
    if payload.cover_url is not None:
        course.cover_url = payload.cover_url or None
        updated = True
    if payload.category_id is not None:
        course.category_id = payload.category_id or None
        updated = True
    if payload.price is not None:
        course.price = payload.price
        updated = True
    if payload.status is not None:
        course.status = payload.status
        updated = True

    if not updated:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")

    db.add(course)
    db.commit()
    db.refresh(course)
    return success(CourseOut.model_validate(course).model_dump(), message="课程已更新")


@router.patch("/{course_id}/status")
def update_course_status(
    course_id: int,
    payload: CourseStatusRequest,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.execute(
        select(Course).where(Course.id == course_id)
    ).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    course.status = payload.status
    db.add(course)
    db.commit()
    db.refresh(course)
    return success(CourseListItem.model_validate(course).model_dump(), message=f"课程状态已变更为 {payload.status.value}")


# ── 课程详情 ──────────────────────────────────────

def _build_chapter_tree(chapters: list[Chapter]) -> list[dict]:
    nodes = {
        chapter.id: ChapterDetailOut.model_validate(chapter).model_dump()
        for chapter in chapters
    }
    tree: list[dict] = []
    for node in nodes.values():
        parent_id = node.get("parent_id")
        if parent_id and parent_id in nodes:
            nodes[parent_id]["children"].append(node)
        else:
            tree.append(node)
    return tree


@router.get("/{course_id}")
def get_course(course_id: int, _: object = Depends(get_current_user), db: Session = Depends(get_db)):
    course = (
        db.execute(
            select(Course)
            .where(Course.id == course_id)
            .options(
                selectinload(Course.category),
                selectinload(Course.chapters).selectinload(Chapter.coursewares),
            )
        )
        .scalar_one_or_none()
    )
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    chapters = _build_chapter_tree(course.chapters)
    payload = {
        **CourseListItem.model_validate(course).model_dump(),
        "category_name": course.category.name if course.category else None,
        "chapters": chapters,
    }
    return success(payload)


# ── 章节 CRUD ─────────────────────────────────────

@router.post("/{course_id}/chapters", status_code=201)
def create_chapter(
    course_id: int,
    payload: ChapterCreate,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    course = db.execute(select(Course).where(Course.id == course_id)).scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    chapter = Chapter(
        course_id=course_id,
        title=payload.title,
        parent_id=payload.parent_id,
        sort_order=payload.sort_order,
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return success(ChapterOut.model_validate(chapter).model_dump(), message="章节已创建")


@router.put("/{course_id}/chapters/{chapter_id}")
def update_chapter(
    course_id: int,
    chapter_id: int,
    payload: ChapterUpdate,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chapter = db.execute(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.course_id == course_id)
    ).scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    updated = False
    if payload.title is not None:
        chapter.title = payload.title
        updated = True
    if payload.parent_id is not None:
        chapter.parent_id = payload.parent_id or None
        updated = True
    if payload.sort_order is not None:
        chapter.sort_order = payload.sort_order
        updated = True

    if not updated:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")

    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return success(ChapterOut.model_validate(chapter).model_dump(), message="章节已更新")


@router.delete("/{course_id}/chapters/{chapter_id}")
def delete_chapter(
    course_id: int,
    chapter_id: int,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chapter = db.execute(
        select(Chapter).where(Chapter.id == chapter_id, Chapter.course_id == course_id)
    ).scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")
    # cascade="all, delete-orphan" 会自动级联删除子章节 + 课件
    db.delete(chapter)
    db.commit()
    return success(message="章节已删除")


# ── 章节排序 ───────────────────────────────────────

@router.put("/{course_id}/chapters/sort")
def sort_chapters(
    course_id: int,
    payload: ChapterSortRequest,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """批量更新章节排序序号。传入 [{id, sort_order}, ...] 按 id 匹配更新。"""
    chapter_ids = {item.id for item in payload.items}
    chapters = db.execute(
        select(Chapter).where(
            Chapter.course_id == course_id,
            Chapter.id.in_(chapter_ids),
        )
    ).scalars().all()

    id_to_chapter = {ch.id: ch for ch in chapters}
    for item in payload.items:
        ch = id_to_chapter.get(item.id)
        if ch:
            ch.sort_order = item.sort_order

    db.commit()
    return success(message="排序已更新")
