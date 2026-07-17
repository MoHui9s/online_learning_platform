"""知识点 CRUD（挂在课程路由下）。"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_teacher
from app.models.course import Course
from app.models.knowledge_point import KnowledgePoint
from app.models.user import User
from app.schemas.common import success
from app.schemas.exam import (
    KnowledgePointCreate,
    KnowledgePointOut,
    KnowledgePointUpdate,
)

router = APIRouter(
    prefix="/courses/{course_id}/knowledge-points", tags=["knowledge-points"]
)


def _build_tree(
    points: list[KnowledgePoint], parent_id: int | None = None
) -> list[dict]:
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
) -> dict:
    """按课程查询知识点树。"""
    points = (
        db.execute(select(KnowledgePoint).where(KnowledgePoint.course_id == course_id))
        .scalars()
        .all()
    )
    return success(_build_tree(list(points)))


@router.post("")
def create_knowledge_point(
    course_id: int,
    payload: KnowledgePointCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_teacher),
) -> dict:
    """创建知识点（教师/admin）。"""
    # 校验课程存在 + parent 属同一课程
    if not db.get(Course, course_id):
        raise HTTPException(status_code=404, detail="课程不存在")
    if payload.parent_id:
        parent = db.get(KnowledgePoint, payload.parent_id)
        if not parent or parent.course_id != course_id:
            raise HTTPException(status_code=400, detail="父知识点不存在或不属于该课程")
    kp = KnowledgePoint(course_id=course_id, **payload.model_dump())
    db.add(kp)
    db.commit()
    db.refresh(kp)
    return success(
        KnowledgePointOut.model_validate(kp).model_dump(), message="创建成功"
    )


@router.put("/{kp_id}")
def update_knowledge_point(
    course_id: int,
    kp_id: int,
    payload: KnowledgePointUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_teacher),
) -> dict:
    """更新知识点。"""
    kp = db.execute(
        select(KnowledgePoint).where(
            KnowledgePoint.id == kp_id, KnowledgePoint.course_id == course_id
        )
    ).scalar_one_or_none()
    if not kp:
        raise HTTPException(status_code=404, detail="知识点不存在")
    # 校验 parent 不能是自己且属于同一课程
    new_parent = payload.model_dump(exclude_unset=True).get("parent_id", None)
    if new_parent is not None and new_parent != kp.parent_id:
        if new_parent == kp_id:
            raise HTTPException(status_code=400, detail="不能将自身设为父知识点")
        if new_parent != 0:  # 0 表示清空 parent
            p = db.get(KnowledgePoint, new_parent)
            if not p or p.course_id != course_id:
                raise HTTPException(
                    status_code=400, detail="父知识点不存在或不属于该课程"
                )
    for key, val in payload.model_dump(exclude_unset=True).items():
        setattr(kp, key, val)
    db.commit()
    db.refresh(kp)
    return success(
        KnowledgePointOut.model_validate(kp).model_dump(), message="更新成功"
    )


@router.delete("/{kp_id}")
def delete_knowledge_point(
    course_id: int,
    kp_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_teacher),
) -> dict:
    """删除知识点。"""
    kp = db.execute(
        select(KnowledgePoint).where(
            KnowledgePoint.id == kp_id, KnowledgePoint.course_id == course_id
        )
    ).scalar_one_or_none()
    if not kp:
        raise HTTPException(status_code=404, detail="知识点不存在")
    # 有子节点禁止删除
    children = (
        db.execute(select(KnowledgePoint).where(KnowledgePoint.parent_id == kp_id))
        .scalars()
        .all()
    )
    if children:
        raise HTTPException(status_code=400, detail="请先删除子知识点")
    # 解除关联绑定
    from app.models.question import QuestionKnowledgePoint

    for qkp in (
        db.execute(
            select(QuestionKnowledgePoint).where(
                QuestionKnowledgePoint.knowledge_point_id == kp_id
            )
        )
        .scalars()
        .all()
    ):
        db.delete(qkp)
    db.delete(kp)
    db.commit()
    return success(message="已删除")
