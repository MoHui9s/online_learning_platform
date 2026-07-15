"""题库 CRUD。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.question import Question, QuestionKnowledgePoint, QuestionType
from app.models.user import User
from app.schemas.common import paginate, success
from app.schemas.exam import QuestionCreate, QuestionOut, QuestionUpdate

router = APIRouter(prefix="/questions", tags=["questions"])


def _sync_knowledge_points(db: Session, question_id: int, kp_ids: list[int]) -> None:
    """同步题目↔知识点关联（先删后插）。"""
    db.execute(
        select(QuestionKnowledgePoint).where(
            QuestionKnowledgePoint.question_id == question_id
        )
    )
    existing = db.execute(
        select(QuestionKnowledgePoint).where(
            QuestionKnowledgePoint.question_id == question_id
        )
    ).scalars().all()
    for e in existing:
        db.delete(e)
    db.flush()
    for kp_id in kp_ids:
        db.add(QuestionKnowledgePoint(question_id=question_id, knowledge_point_id=kp_id))
    db.flush()


@router.get("")
def list_questions(
    course_id: int,
    type: QuestionType | None = Query(None),
    difficulty: int | None = Query(None, ge=1, le=5),
    knowledge_point_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """按课程分页查题目，支持类型/难度/知识点筛选。"""
    stmt = select(Question).where(Question.course_id == course_id)
    if type:
        stmt = stmt.where(Question.type == type)
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)
    if knowledge_point_id:
        stmt = stmt.join(
            QuestionKnowledgePoint,
            QuestionKnowledgePoint.question_id == Question.id,
        ).where(QuestionKnowledgePoint.knowledge_point_id == knowledge_point_id)

    total = db.execute(
        select(Question).where(Question.course_id == course_id)
    ).scalars().count()  # 简化版，生产应加 count 子查询
    # Recalculate with filters
    sub = stmt
    total_stmt = select(Question.id).where(Question.course_id == course_id)
    if type:
        total_stmt = total_stmt.where(Question.type == type)
    if difficulty:
        total_stmt = total_stmt.where(Question.difficulty == difficulty)
    if knowledge_point_id:
        total_stmt = total_stmt.join(
            QuestionKnowledgePoint,
            QuestionKnowledgePoint.question_id == Question.id,
        ).where(QuestionKnowledgePoint.knowledge_point_id == knowledge_point_id)
    total = len(db.execute(total_stmt).scalars().all())

    items = db.execute(
        stmt.offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    result = []
    for q in items:
        kp_ids = [
            qkp.knowledge_point_id
            for qkp in db.execute(
                select(QuestionKnowledgePoint).where(
                    QuestionKnowledgePoint.question_id == q.id
                )
            ).scalars().all()
        ]
        d = QuestionOut.model_validate(q).model_dump()
        d["knowledge_point_ids"] = kp_ids
        result.append(d)

    return success(paginate(result, total, page, page_size))


@router.get("/{question_id}")
def get_question(
    question_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """题目详情。"""
    q = db.execute(
        select(Question).where(Question.id == question_id)
    ).scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")
    kp_ids = [
        qkp.knowledge_point_id
        for qkp in db.execute(
            select(QuestionKnowledgePoint).where(
                QuestionKnowledgePoint.question_id == q.id
            )
        ).scalars().all()
    ]
    d = QuestionOut.model_validate(q).model_dump()
    d["knowledge_point_ids"] = kp_ids
    return success(d)


@router.post("")
def create_question(
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """创建题目（教师/admin）。"""
    q = Question(
        course_id=payload.course_id,
        type=payload.type,
        stem=payload.stem,
        options=payload.options,
        answer=payload.answer,
        analysis=payload.analysis,
        difficulty=payload.difficulty,
        score=payload.score,
        created_by=current.id,
    )
    db.add(q)
    db.flush()
    _sync_knowledge_points(db, q.id, payload.knowledge_point_ids)
    db.commit()
    db.refresh(q)

    d = QuestionOut.model_validate(q).model_dump()
    d["knowledge_point_ids"] = payload.knowledge_point_ids
    return success(d, message="创建成功")


@router.put("/{question_id}")
def update_question(
    question_id: int,
    payload: QuestionUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """更新题目。"""
    q = db.execute(
        select(Question).where(Question.id == question_id)
    ).scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")

    update_data = payload.model_dump(exclude_unset=True)
    kp_ids = update_data.pop("knowledge_point_ids", None)

    for key, val in update_data.items():
        setattr(q, key, val)

    if kp_ids is not None:
        _sync_knowledge_points(db, q.id, kp_ids)

    db.commit()
    db.refresh(q)

    kp_ids_final = [
        qkp.knowledge_point_id
        for qkp in db.execute(
            select(QuestionKnowledgePoint).where(
                QuestionKnowledgePoint.question_id == q.id
            )
        ).scalars().all()
    ]
    d = QuestionOut.model_validate(q).model_dump()
    d["knowledge_point_ids"] = kp_ids_final
    return success(d, message="更新成功")


@router.delete("/{question_id}")
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """删除题目。"""
    q = db.execute(
        select(Question).where(Question.id == question_id)
    ).scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="题目不存在")

    # 删除知识点关联
    for qkp in db.execute(
        select(QuestionKnowledgePoint).where(
            QuestionKnowledgePoint.question_id == question_id
        )
    ).scalars().all():
        db.delete(qkp)

    db.delete(q)
    db.commit()
    return success(message="已删除")
