"""课程 Service：CRUD + Redis 缓存（列表 TTL 5 分钟）。"""
import json

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.redis import get_redis
from app.models.course import Course, CourseStatus
from app.models.user import User

_LIST_TTL = 300  # 5 分钟


def _cache_key(page: int, page_size: int, keyword: str | None, category_id: int | None, status: str | None) -> str:
    return f"courses:list:{page}:{page_size}:{keyword or ''}:{category_id or ''}:{status or ''}"


def _dump_course(c: Course) -> dict:
    return {
        "id": c.id,
        "title": c.title,
        "description": c.description,
        "cover_url": c.cover_url,
        "category_id": c.category_id,
        "teacher_id": c.teacher_id,
        "status": c.status.value,
        "price": float(c.price),
        "student_count": c.student_count,
        "created_at": c.created_at.isoformat(),
    }


def _clear_list_cache() -> None:
    r = get_redis()
    for key in r.scan_iter("courses:list:*"):
        r.delete(key)


def _build_filters(keyword=None, category_id=None, status=None):
    filters = []
    if keyword:
        filters.append(or_(Course.title.contains(keyword), Course.description.contains(keyword)))
    if category_id is not None:
        filters.append(Course.category_id == category_id)
    if status:
        filters.append(Course.status == status)
    return filters


# ─── 查询 ───────────────────────────────────────────────
def get_list(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    keyword: str | None = None,
    category_id: int | None = None,
    status: str | None = None,
) -> tuple[list, int]:
    """分页课程列表，优先读 Redis 缓存。"""
    r = get_redis()
    ck = _cache_key(page, page_size, keyword, category_id, status)
    cached = r.get(ck)
    if cached:
        data = json.loads(cached)
        return data["items"], data["total"]

    filters = _build_filters(keyword, category_id, status)

    total = db.execute(select(func.count()).select_from(Course).where(*filters)).scalar()

    rows = db.execute(
        select(Course)
        .where(*filters)
        .order_by(Course.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    items = [_dump_course(r) for r in rows]
    r.setex(ck, _LIST_TTL, json.dumps({"items": items, "total": total}, ensure_ascii=False))
    return items, total


def get_detail(db: Session, course_id: int) -> Course:
    course = db.execute(
        select(Course)
        .options(joinedload(Course.category), joinedload(Course.chapters))
        .where(Course.id == course_id)
    ).unique().scalar_one_or_none()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    return course


def get_by_id(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    return course


# ─── 写 ─────────────────────────────────────────────────
def create_course(db: Session, teacher: User, **kwargs) -> Course:
    course = Course(teacher_id=teacher.id, **kwargs)
    db.add(course)
    db.commit()
    db.refresh(course)
    _clear_list_cache()
    return course


def update_course(db: Session, course_id: int, data: dict) -> Course:
    course = get_by_id(db, course_id)
    for field, value in data.items():
        if value is not None:
            setattr(course, field, value)
    db.commit()
    db.refresh(course)
    _clear_list_cache()
    return course


def delete_course(db: Session, course_id: int) -> None:
    course = get_by_id(db, course_id)
    db.delete(course)
    db.commit()
    _clear_list_cache()
