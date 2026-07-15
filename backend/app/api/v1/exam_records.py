"""考试作答：开始考试 / 提交答案 / 查看记录。"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.exam import Exam, ExamQuestion, ExamRecord, ExamRecordStatus, ExamStatus
from app.models.question import Question
from app.models.user import User
from app.schemas.common import paginate, success
from app.schemas.exam import (
    ExamRecordDetailOut,
    ExamRecordOut,
    ExamStartResponse,
    ExamSubmitRequest,
    QuestionBrief,
    QuestionOut,
)
from app.services.exam_service import grade_and_persist

router = APIRouter(prefix="/exam-records", tags=["exam-records"])


@router.post("/{exam_id}/start")
def start_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """开始考试：创建作答记录，返回题目（不含答案）。"""
    exam = db.execute(
        select(Exam).where(Exam.id == exam_id)
    ).scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if exam.status != ExamStatus.published:
        raise HTTPException(status_code=400, detail="考试未发布")

    # 检查是否已有进行中的记录
    existing = db.execute(
        select(ExamRecord).where(
            ExamRecord.exam_id == exam_id,
            ExamRecord.user_id == current.id,
            ExamRecord.status == ExamRecordStatus.in_progress,
        )
    ).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if existing:
        # 返回已有记录
        eq_rows = db.execute(
            select(ExamQuestion, Question)
            .join(Question, Question.id == ExamQuestion.question_id)
            .where(ExamQuestion.exam_id == exam.id)
            .order_by(ExamQuestion.sort_order)
        ).all()
        questions = []
        for eq, q in eq_rows:
            d = QuestionBrief.model_validate(q).model_dump()
            d["score"] = eq.score
            questions.append(d)
        return success(
            ExamStartResponse(
                record_id=existing.id, started_at=existing.started_at, questions=questions
            ).model_dump()
        )

    # 创建新记录
    record = ExamRecord(
        exam_id=exam_id,
        user_id=current.id,
        started_at=now,
        status=ExamRecordStatus.in_progress,
    )
    db.add(record)
    db.flush()

    eq_rows = db.execute(
        select(ExamQuestion, Question)
        .join(Question, Question.id == ExamQuestion.question_id)
        .where(ExamQuestion.exam_id == exam.id)
        .order_by(ExamQuestion.sort_order)
    ).all()

    questions = []
    for eq, q in eq_rows:
        d = QuestionBrief.model_validate(q).model_dump()
        d["score"] = eq.score
        questions.append(d)

    db.commit()
    return success(
        ExamStartResponse(
            record_id=record.id, started_at=now, questions=questions
        ).model_dump()
    )


@router.post("/{record_id}/submit")
def submit_exam(
    record_id: int,
    payload: ExamSubmitRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """提交答案，自动阅卷（客观题）。"""
    record = db.execute(
        select(ExamRecord).where(ExamRecord.id == record_id)
    ).scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    if record.user_id != current.id:
        raise HTTPException(status_code=403, detail="不可提交他人考试")
    if record.status != ExamRecordStatus.in_progress:
        raise HTTPException(status_code=400, detail="考试已提交")

    # 组装答案
    answers = {str(a.question_id): a.answer for a in payload.answers}
    record.answers = answers

    # 自动阅卷
    score = grade_and_persist(db, record, answers)

    return success(
        {"score": score, "status": record.status}, message="提交成功"
    )


@router.get("/{exam_id}/my-records")
def my_records(
    exam_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """当前用户的考试记录列表。"""
    records = db.execute(
        select(ExamRecord)
        .where(ExamRecord.exam_id == exam_id, ExamRecord.user_id == current.id)
        .order_by(ExamRecord.created_at.desc())
    ).scalars().all()
    return success(
        [ExamRecordOut.model_validate(r).model_dump() for r in records]
    )


@router.get("/{record_id}")
def get_record(
    record_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """作答详情（含题目 + 答案，交卷后可见）。"""
    record = db.execute(
        select(ExamRecord).where(ExamRecord.id == record_id)
    ).scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    if record.user_id != current.id:
        raise HTTPException(status_code=403, detail="不可查看他人记录")

    eq_rows = db.execute(
        select(ExamQuestion, Question)
        .join(Question, Question.id == ExamQuestion.question_id)
        .where(ExamQuestion.exam_id == record.exam_id)
        .order_by(ExamQuestion.sort_order)
    ).all()

    questions = []
    for eq, q in eq_rows:
        d = QuestionOut.model_validate(q).model_dump()
        d["score"] = eq.score
        questions.append(d)

    result = ExamRecordDetailOut.model_validate(record).model_dump()
    result["questions"] = questions
    return success(result)
