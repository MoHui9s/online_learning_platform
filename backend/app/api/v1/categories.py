"""分类管理路由：CRUD + 分类树。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.category import Category
from app.schemas.common import success
from app.schemas.course import CategoryCreate, CategoryOut, CategoryUpdate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", status_code=201)
def create_category(
    payload: CategoryCreate,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category = Category(
        name=payload.name,
        parent_id=payload.parent_id,
        sort_order=payload.sort_order,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return success(CategoryOut.model_validate(category).model_dump(), message="分类已创建")


@router.put("/{category_id}")
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    category = db.execute(
        select(Category).where(Category.id == category_id)
    ).scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    updated = False
    if payload.name is not None:
        category.name = payload.name
        updated = True
    if payload.parent_id is not None:
        category.parent_id = payload.parent_id or None
        updated = True
    if payload.sort_order is not None:
        category.sort_order = payload.sort_order
        updated = True

    if not updated:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")

    db.add(category)
    db.commit()
    db.refresh(category)
    return success(CategoryOut.model_validate(category).model_dump(), message="分类已更新")


@router.get("/tree")
def category_tree(
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """返回递归嵌套的分类树（适于前端级联/tree 组件）。"""
    categories = (
        db.execute(
            select(Category).order_by(Category.sort_order.asc(), Category.id.asc())
        )
        .scalars()
        .all()
    )

    nodes: dict[int, dict] = {}
    for cat in categories:
        nodes[cat.id] = CategoryOut.model_validate(cat).model_dump()

    tree: list[dict] = []
    for node in nodes.values():
        parent_id = node.get("parent_id")
        if parent_id and parent_id in nodes:
            nodes[parent_id]["children"].append(node)
        else:
            tree.append(node)

    return success(tree)
