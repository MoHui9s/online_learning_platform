"""错题本 API（C3）。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.exam import WrongQuestion
from app.models.question import Question
from app.models.user import User
from app.schemas.common import paginate, success
from app.schemas.exam import QuestionBrief, WrongQuestionOut

router = APIRouter(tags=["wrong-questions"])


@router.get("/my/wrong-questions")
def list_wrong_questions(
    course_id: int | None = Query(None),
    is_mastered: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    """我的错题列表，按课程/掌握状态筛选分页。"""
    if course_id:
        stmt = (
            select(WrongQuestion)
            .join(Question, Question.id == WrongQuestion.question_id)
            .where(WrongQuestion.user_id == current.id, Question.course_id == course_id)
        )
        count_stmt = (
            select(WrongQuestion.id)
            .join(Question, Question.id == WrongQuestion.question_id)
            .where(WrongQuestion.user_id == current.id, Question.course_id == course_id)
        )
    else:
        stmt = select(WrongQuestion).where(WrongQuestion.user_id == current.id)
        count_stmt = select(WrongQuestion.id).where(WrongQuestion.user_id == current.id)

    if is_mastered is not None:
        stmt = stmt.where(WrongQuestion.is_mastered == is_mastered)
        count_stmt = count_stmt.where(WrongQuestion.is_mastered == is_mastered)

    total = len(db.execute(count_stmt).scalars().all())

    items = db.execute(
        stmt.order_by(WrongQuestion.last_wrong_at.desc().nullslast())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    result = []
    for wq in items:
        q = db.get(Question, wq.question_id)
        d = WrongQuestionOut.model_validate(wq).model_dump()
        d["question"] = QuestionBrief.model_validate(q).model_dump() if q else None
        result.append(d)

    return success(paginate(result, total, page, page_size))


@router.put("/wrong-questions/{wq_id}/master")
def mark_mastered(
    wq_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    """标记错题为已掌握。"""
    wq = db.execute(
        select(WrongQuestion).where(
            WrongQuestion.id == wq_id, WrongQuestion.user_id == current.id
        )
    ).scalar_one_or_none()
    if not wq:
        raise HTTPException(status_code=404, detail="错题记录不存在")
    wq.is_mastered = True
    db.commit()
    return success(message="已标记为掌握")


@router.delete("/wrong-questions/{wq_id}")
def delete_wrong_question(
    wq_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    """移除错题记录。"""
    wq = db.execute(
        select(WrongQuestion).where(
            WrongQuestion.id == wq_id, WrongQuestion.user_id == current.id
        )
    ).scalar_one_or_none()
    if not wq:
        raise HTTPException(status_code=404, detail="错题记录不存在")
    db.delete(wq)
    db.commit()
    return success(message="已移除")
