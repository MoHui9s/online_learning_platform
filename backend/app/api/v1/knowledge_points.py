"""知识点 CRUD。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.knowledge_point import KnowledgePoint
from app.models.user import User
from app.schemas.common import success
from app.schemas.exam import KnowledgePointCreate, KnowledgePointOut, KnowledgePointUpdate

router = APIRouter(prefix="/knowledge-points", tags=["knowledge-points"])


def _build_tree(points: list[KnowledgePoint], parent_id: int | None = None) -> list[dict]:
    """递归构建知识点树。"""
    result = []
    for p in points:
        if p.parent_id == parent_id:
            d = KnowledgePointOut.model_validate(p).model_dump()
            d["children"] = _build_tree(points, p.id)
            result.append(d)
    return result


@router.get("")
def list_knowledge_points(
    course_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """按课程查询知识点树。"""
    points = db.execute(
        select(KnowledgePoint).where(KnowledgePoint.course_id == course_id)
    ).scalars().all()
    return success(_build_tree(list(points)))


@router.post("")
def create_knowledge_point(
    payload: KnowledgePointCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """创建知识点（教师/admin）。"""
    kp = KnowledgePoint(**payload.model_dump())
    db.add(kp)
    db.commit()
    db.refresh(kp)
    return success(KnowledgePointOut.model_validate(kp).model_dump(), message="创建成功")


@router.put("/{kp_id}")
def update_knowledge_point(
    kp_id: int,
    payload: KnowledgePointUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """更新知识点。"""
    kp = db.execute(
        select(KnowledgePoint).where(KnowledgePoint.id == kp_id)
    ).scalar_one_or_none()
    if not kp:
        raise HTTPException(status_code=404, detail="知识点不存在")
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(kp, key, val)
    db.commit()
    db.refresh(kp)
    return success(KnowledgePointOut.model_validate(kp).model_dump(), message="更新成功")


@router.delete("/{kp_id}")
def delete_knowledge_point(
    kp_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """删除知识点。"""
    kp = db.execute(
        select(KnowledgePoint).where(KnowledgePoint.id == kp_id)
    ).scalar_one_or_none()
    if not kp:
        raise HTTPException(status_code=404, detail="知识点不存在")
    db.delete(kp)
    db.commit()
    return success(message="已删除")
