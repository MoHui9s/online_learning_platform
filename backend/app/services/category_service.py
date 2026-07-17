"""课程分类 Service：分类树 CRUD。"""

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.course import Course


def get_tree(db: Session) -> list[dict]:
    """返回二级分类树（parent 为 null 的行作为一级，children 含下级）。"""

    def _node(cat: Category) -> dict:
        return {
            "id": cat.id,
            "name": cat.name,
            "parent_id": cat.parent_id,
            "sort_order": cat.sort_order,
            "created_at": cat.created_at,
            "children": [_node(c) for c in cat.children] if cat.children else None,
        }

    roots = (
        db.execute(
            select(Category)
            .where(Category.parent_id.is_(None))
            .order_by(Category.sort_order)
        )
        .scalars()
        .all()
    )

    return [_node(r) for r in roots]


def get_by_id(db: Session, category_id: int) -> Category:
    cat = db.get(Category, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="分类不存在")
    return cat


def create(db: Session, name: str, parent_id: int | None, sort_order: int) -> Category:
    if parent_id:
        parent = db.get(Category, parent_id)
        if not parent:
            raise HTTPException(status_code=404, detail="父分类不存在")
        # 只允许二级（父的父必须是 null）
        if parent.parent_id is not None:
            raise HTTPException(status_code=400, detail="仅支持二级分类")
    cat = Category(name=name, parent_id=parent_id, sort_order=sort_order)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


def update(
    db: Session,
    category_id: int,
    name: str | None,
    parent_id: int | None,
    sort_order: int | None,
) -> Category:
    cat = get_by_id(db, category_id)
    if name is not None:
        cat.name = name
    if parent_id is not None:
        if parent_id == category_id:
            raise HTTPException(status_code=400, detail="不能把自己设为父分类")
        cat.parent_id = parent_id
    if sort_order is not None:
        cat.sort_order = sort_order
    db.commit()
    db.refresh(cat)
    return cat


def delete(db: Session, category_id: int) -> None:
    cat = get_by_id(db, category_id)
    # 拦截：有子分类
    if cat.children:
        raise HTTPException(
            status_code=400, detail="该分类下存在子分类，请先删除子分类"
        )
    # 拦截：有关联课程
    course_count = db.execute(
        select(func.count())
        .select_from(Course)
        .where(Course.category_id == category_id)
    ).scalar()
    if course_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该分类下关联了 {course_count} 门课程，请先迁移课程到其他分类",
        )
    db.delete(cat)
    db.commit()
