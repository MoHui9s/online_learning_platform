"""课程分类路由：GET /categories、POST/PUT/DELETE /categories/{id}。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.schemas.common import success
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("")
def list_categories(db: Session = Depends(get_db)):
    """分类树（公开，无需认证也可浏览；此处默认需登录获取上下文）。"""
    tree = category_service.get_tree(db)
    return success(tree)


@router.post("")
def create_category(
    payload: CategoryCreate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    cat = category_service.create(db, payload.name, payload.parent_id, payload.sort_order)
    return success(CategoryOut.model_validate(cat).model_dump(), message="分类创建成功")


@router.put("/{category_id}")
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    cat = category_service.update(db, category_id, payload.name, payload.parent_id, payload.sort_order)
    return success(CategoryOut.model_validate(cat).model_dump(), message="分类已更新")


@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    category_service.delete(db, category_id)
    return success(message="分类已删除")
