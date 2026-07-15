"""考试管理 + 组卷 + 开考/交卷 + 成绩（C2 完整模块）。"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.exam import Exam, ExamQuestion, ExamRecord, ExamRecordStatus, ExamStatus
from app.models.question import Question
from app.models.user import User, UserRole
from app.schemas.common import paginate, success
from app.schemas.exam import (
    AnswerSubmit,
    ExamCreate,
    ExamDetailOut,
    ExamOut,
    ExamPreviewOut,
    ExamRecordDetailOut,
    ExamRecordOut,
    ExamSetQuestions,
    ExamStartResponse,
    ExamSubmitRequest,
    ExamUpdate,
    QuestionBrief,
    QuestionOut,
)
from app.services.exam_service import grade_and_persist

router = APIRouter(prefix="/exams", tags=["exams"])


def _role_check(user: User) -> None:
    """仅教师/admin 可操作考试管理。"""
    if user.role not in (UserRole.teacher, UserRole.admin):
        raise HTTPException(status_code=403, detail="仅教师/管理员可操作")


def _build_exam_detail(exam: Exam, db: Session) -> dict:
    """组装考试详情（含题目 + 分值，教师视角）。"""
    eq_rows = db.execute(
        select(ExamQuestion, Question)
        .join(Question, Question.id == ExamQuestion.question_id)
        .where(ExamQuestion.exam_id == exam.id)
        .order_by(ExamQuestion.sort_order)
    ).all()
    questions = []
    for eq, q in eq_rows:
        d = QuestionOut.model_validate(q).model_dump()
        d["score"] = eq.score
        questions.append(d)
    result = ExamDetailOut.model_validate(exam).model_dump()
    result["questions"] = questions
    result["question_count"] = len(questions)
    return result


def _build_exam_preview(exam: Exam, db: Session) -> dict:
    """组装学生视角预览（不含答案）。"""
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
    result = ExamPreviewOut.model_validate(exam).model_dump()
    result["questions"] = questions
    result["question_count"] = len(questions)
    return result


# ===================== 考试 CRUD =====================


@router.get("")
def list_exams(
    course_id: int,
    status: ExamStatus | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    """按课程分页查考试列表。"""
    stmt = select(Exam).where(Exam.course_id == course_id)
    count_stmt = select(Exam.id).where(Exam.course_id == course_id)
    if status:
        stmt = stmt.where(Exam.status == status)
        count_stmt = count_stmt.where(Exam.status == status)

    total = len(db.execute(count_stmt).scalars().all())
    items = db.execute(
        stmt.order_by(Exam.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    result = []
    for exam in items:
        qc = len(
            db.execute(select(ExamQuestion.id).where(ExamQuestion.exam_id == exam.id)).scalars().all()
        )
        d = ExamOut.model_validate(exam).model_dump()
        d["question_count"] = qc
        result.append(d)

    return success(paginate(result, total, page, page_size))


@router.post("")
def create_exam(
    payload: ExamCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    """创建考试。"""
    _role_check(current)
    exam = Exam(
        course_id=payload.course_id,
        title=payload.title,
        description=payload.description,
        duration_minutes=payload.duration_minutes,
        total_score=payload.total_score,
        pass_score=payload.pass_score,
        start_time=payload.start_time,
        end_time=payload.end_time,
        created_by=current.id,
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return success(ExamOut.model_validate(exam).model_dump(), message="创建成功")


@router.get("/{exam_id}")
def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    """考试详情（教师含答案，学生不含）。"""
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if current.role in (UserRole.teacher, UserRole.admin):
        return success(_build_exam_detail(exam, db))
    return success(_build_exam_preview(exam, db))


@router.put("/{exam_id}")
def update_exam(
    exam_id: int,
    payload: ExamUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    """更新考试（仅草稿状态）。"""
    _role_check(current)
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if exam.status != ExamStatus.draft:
        raise HTTPException(status_code=400, detail="仅草稿状态可修改")

    update_data = payload.model_dump(exclude_unset=True)
    questions = update_data.pop("questions", None)
    for key, val in update_data.items():
        setattr(exam, key, val)

    if questions is not None:
        for eq in db.execute(
            select(ExamQuestion).where(ExamQuestion.exam_id == exam.id)
        ).scalars().all():
            db.delete(eq)
        db.flush()
        for item in questions:
            db.add(
                ExamQuestion(
                    exam_id=exam.id,
                    question_id=item["question_id"],
                    score=item["score"],
                    sort_order=item["sort_order"],
                )
            )

    db.commit()
    db.refresh(exam)
    return success(_build_exam_detail(exam, db), message="更新成功")


@router.delete("/{exam_id}")
def delete_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    """删除考试（仅草稿）。"""
    _role_check(current)
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if exam.status != ExamStatus.draft:
        raise HTTPException(status_code=400, detail="仅草稿状态可删除")

    for eq in db.execute(
        select(ExamQuestion).where(ExamQuestion.exam_id == exam.id)
    ).scalars().all():
        db.delete(eq)
    db.delete(exam)
    db.commit()
    return success(message="已删除")


@router.post("/{exam_id}/publish")
def publish_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    """发布考试。"""
    _role_check(current)
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if exam.status != ExamStatus.draft:
        raise HTTPException(status_code=400, detail="仅草稿状态可发布")

    qc = len(
        db.execute(
            select(ExamQuestion.id).where(ExamQuestion.exam_id == exam.id)
        ).scalars().all()
    )
    if qc == 0:
        raise HTTPException(status_code=400, detail="考试须至少包含一道题目")

    exam.status = ExamStatus.published
    db.commit()
    return success(message="已发布")


# ===================== 组卷 =====================


@router.post("/{exam_id}/questions")
def set_exam_questions(
    exam_id: int,
    payload: ExamSetQuestions,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    """组卷：向考试添加题目（含分值+题序）。"""
    _role_check(current)
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if exam.status != ExamStatus.draft:
        raise HTTPException(status_code=400, detail="仅草稿状态可组卷")

    # 先删旧再插新
    for eq in db.execute(
        select(ExamQuestion).where(ExamQuestion.exam_id == exam.id)
    ).scalars().all():
        db.delete(eq)
    db.flush()

    for item in payload.questions:
        db.add(
            ExamQuestion(
                exam_id=exam.id,
                question_id=item.question_id,
                score=item.score,
                sort_order=item.sort_order,
            )
        )
    db.commit()
    return success(_build_exam_detail(exam, db), message="组卷成功")


# ===================== 学生开考 / 交卷 =====================


@router.post("/{exam_id}/start")
def start_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    """学生开考：校验窗口期，返回题目（不含答案），创建作答记录。"""
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if exam.status != ExamStatus.published:
        raise HTTPException(status_code=400, detail="考试未发布")

    # 检查窗口期
    now = datetime.now(timezone.utc)
    if exam.start_time and now < exam.start_time:
        raise HTTPException(status_code=400, detail="考试尚未开放")
    if exam.end_time and now > exam.end_time:
        raise HTTPException(status_code=400, detail="考试已结束")

    # 检查是否已有进行中记录（幂等：返回已有记录）
    existing = db.execute(
        select(ExamRecord).where(
            ExamRecord.exam_id == exam_id,
            ExamRecord.user_id == current.id,
            ExamRecord.status == ExamRecordStatus.in_progress,
        )
    ).scalar_one_or_none()

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

    if existing:
        return success(
            ExamStartResponse(
                record_id=existing.id, started_at=existing.started_at, questions=questions
            ).model_dump(),
            message="继续作答",
        )

    record = ExamRecord(
        exam_id=exam_id,
        user_id=current.id,
        started_at=now,
        status=ExamRecordStatus.in_progress,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return success(
        ExamStartResponse(record_id=record.id, started_at=now, questions=questions).model_dump()
    )


@router.post("/{exam_id}/submit")
def submit_exam(
    exam_id: int,
    payload: ExamSubmitRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    """交卷：自动阅卷（客观题），写入错题本。"""
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    # 查找当前用户该考试的进行中记录
    record = db.execute(
        select(ExamRecord).where(
            ExamRecord.exam_id == exam_id,
            ExamRecord.user_id == current.id,
            ExamRecord.status == ExamRecordStatus.in_progress,
        )
    ).scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=400, detail="无进行中的考试记录")

    # 超时判断
    if record.started_at and exam.duration_minutes:
        elapsed = (datetime.now(timezone.utc) - record.started_at).total_seconds() / 60
        if elapsed > exam.duration_minutes:
            raise HTTPException(status_code=400, detail="考试已超时，不可交卷")

    answers = {str(a.question_id): a.answer for a in payload.answers}
    record.answers = answers
    score = grade_and_persist(db, record, answers)

    return success({"score": score, "status": record.status}, message="交卷成功")


# ===================== 成绩查询 =====================


@router.get("/{exam_id}/result")
def exam_result(
    exam_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    """教师看全班成绩。"""
    _role_check(current)
    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    records = db.execute(
        select(ExamRecord).where(ExamRecord.exam_id == exam_id)
    ).scalars().all()

    return success([ExamRecordOut.model_validate(r).model_dump() for r in records])


# ===================== 我的考试记录（学生） =====================

my_router = APIRouter(prefix="/my/exam-records", tags=["my-exam-records"])


@my_router.get("")
def my_exam_records(
    exam_id: int | None = Query(None),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    """当前用户的所有考试记录。"""
    stmt = select(ExamRecord).where(ExamRecord.user_id == current.id)
    if exam_id:
        stmt = stmt.where(ExamRecord.exam_id == exam_id)
    records = db.execute(stmt.order_by(ExamRecord.created_at.desc())).scalars().all()
    return success([ExamRecordOut.model_validate(r).model_dump() for r in records])


@my_router.get("/{record_id}")
def my_exam_record_detail(
    record_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> dict:
    """单条考试记录详情（含题目与答案，交卷后可见）。"""
    record = db.get(ExamRecord, record_id)
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
