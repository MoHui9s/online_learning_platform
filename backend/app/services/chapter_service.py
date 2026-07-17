"""章节 Service：树形章节 CRUD。"""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chapter import Chapter
from app.services.course_service import get_by_id as get_course


def get_chapters_by_course(db: Session, course_id: int) -> list[dict]:
    """返回课程章节树。"""

    def _node(ch: Chapter) -> dict:
        return {
            "id": ch.id,
            "course_id": ch.course_id,
            "parent_id": ch.parent_id,
            "title": ch.title,
            "sort_order": ch.sort_order,
            "created_at": ch.created_at,
            "children": [_node(c) for c in ch.children] if ch.children else None,
        }

    roots = (
        db.execute(
            select(Chapter)
            .where(Chapter.course_id == course_id, Chapter.parent_id.is_(None))
            .order_by(Chapter.sort_order)
        )
        .scalars()
        .all()
    )

    return [_node(r) for r in roots]


def get_by_id(db: Session, chapter_id: int) -> Chapter:
    ch = db.get(Chapter, chapter_id)
    if not ch:
        raise HTTPException(status_code=404, detail="章节不存在")
    return ch


def create(
    db: Session,
    course_id: int,
    title: str,
    parent_id: int | None,
    sort_order: int,
) -> Chapter:
    get_course(db, course_id)  # 校验课程存在
    if parent_id:
        parent = db.get(Chapter, parent_id)
        if not parent or parent.course_id != course_id:
            raise HTTPException(status_code=400, detail="父章节不存在或不属于该课程")
    ch = Chapter(
        course_id=course_id, title=title, parent_id=parent_id, sort_order=sort_order
    )
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ch


def update(
    db: Session,
    chapter_id: int,
    title: str | None,
    parent_id: int | None,
    sort_order: int | None,
) -> Chapter:
    ch = get_by_id(db, chapter_id)
    if title is not None:
        ch.title = title
    if parent_id is not None:
        if parent_id == chapter_id:
            raise HTTPException(status_code=400, detail="不能把自己设为父章节")
        ch.parent_id = parent_id
    if sort_order is not None:
        ch.sort_order = sort_order
    db.commit()
    db.refresh(ch)
    return ch


def delete(db: Session, chapter_id: int) -> None:
    ch = get_by_id(db, chapter_id)
    if ch.children:
        raise HTTPException(status_code=400, detail="请先删除子章节")
    db.delete(ch)
    db.commit()


def batch_sort(db: Session, course_id: int, sort_items: list[dict]) -> list[Chapter]:
    """批量更新章节 sort_order。sort_items: [{id: int, sort_order: int}, ...]"""
    chapter_ids = {item["id"] for item in sort_items}
    chapters = (
        db.execute(
            select(Chapter).where(
                Chapter.id.in_(chapter_ids), Chapter.course_id == course_id
            )
        )
        .scalars()
        .all()
    )
    if len(chapters) != len(chapter_ids):
        raise HTTPException(status_code=400, detail="部分章节不存在或不属于该课程")
    chapter_map = {ch.id: ch for ch in chapters}
    for item in sort_items:
        chapter_map[item["id"]].sort_order = item["sort_order"]
    db.commit()
    return chapters
