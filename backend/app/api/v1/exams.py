"""考试管理：组卷、发布、查看。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.exam import Exam, ExamQuestion, ExamStatus
from app.models.question import Question
from app.models.user import User, UserRole
from app.schemas.common import paginate, success
from app.schemas.exam import (
    ExamCreate,
    ExamDetailOut,
    ExamOut,
    ExamPreviewOut,
    ExamUpdate,
    QuestionBrief,
    QuestionOut,
)

router = APIRouter(prefix="/exams", tags=["exams"])


def _role_check(user: User) -> None:
    """仅教师/admin 可操作考试管理。"""
    if user.role not in (UserRole.teacher, UserRole.admin):
        raise HTTPException(status_code=403, detail="仅教师/管理员可操作")


def _build_exam_detail(exam: Exam, db: Session) -> dict:
    """组装考试详情（含题目列表 + 分值）。"""
    eq_rows = db.execute(
        select(ExamQuestion, Question)
        .join(Question, Question.id == ExamQuestion.question_id)
        .where(ExamQuestion.exam_id == exam.id)
        .order_by(ExamQuestion.sort_order)
    ).all()

    questions = []
    for eq, q in eq_rows:
        d = QuestionOut.model_validate(q).model_dump()
        d["score"] = eq.score  # 覆盖为试卷分值
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


@router.get("")
def list_exams(
    course_id: int,
    status: ExamStatus | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """按课程分页查考试列表。"""
    stmt = select(Exam).where(Exam.course_id == course_id)
    if status:
        stmt = stmt.where(Exam.status == status)
    stmt = stmt.order_by(Exam.created_at.desc())

    total = len(
        db.execute(
            select(Exam.id).where(Exam.course_id == course_id)
        ).scalars().all()
    )

    items = db.execute(
        stmt.offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    result = []
    for exam in items:
        qc = len(
            db.execute(
                select(ExamQuestion.id).where(ExamQuestion.exam_id == exam.id)
            ).scalars().all()
        )
        d = ExamOut.model_validate(exam).model_dump()
        d["question_count"] = qc
        result.append(d)

    return success(paginate(result, total, page, page_size))


@router.get("/{exam_id}")
def get_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """考试详情（教师视角含答案，学生视角不含）。"""
    exam = db.execute(
        select(Exam).where(Exam.id == exam_id)
    ).scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    if current.role in (UserRole.teacher, UserRole.admin):
        return success(_build_exam_detail(exam, db))
    else:
        return success(_build_exam_preview(exam, db))


@router.post("")
def create_exam(
    payload: ExamCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """创建考试（含组卷）。"""
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
    db.flush()

    # 组卷：批量插入 exam_questions
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
    db.refresh(exam)
    return success(_build_exam_detail(exam, db), message="创建成功")


@router.put("/{exam_id}")
def update_exam(
    exam_id: int,
    payload: ExamUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """更新考试（仅草稿状态可改）。"""
    _role_check(current)

    exam = db.execute(
        select(Exam).where(Exam.id == exam_id)
    ).scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if exam.status != ExamStatus.draft:
        raise HTTPException(status_code=400, detail="仅草稿状态可修改")

    update_data = payload.model_dump(exclude_unset=True)
    questions = update_data.pop("questions", None)

    for key, val in update_data.items():
        setattr(exam, key, val)

    if questions is not None:
        # 先删后插
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
):
    """删除考试（仅草稿）。"""
    _role_check(current)

    exam = db.execute(
        select(Exam).where(Exam.id == exam_id)
    ).scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if exam.status != ExamStatus.draft:
        raise HTTPException(status_code=400, detail="仅草稿状态可删除")

    # 删除关联
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
):
    """发布考试。"""
    _role_check(current)

    exam = db.execute(
        select(Exam).where(Exam.id == exam_id)
    ).scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if exam.status != ExamStatus.draft:
        raise HTTPException(status_code=400, detail="仅草稿状态可发布")

    # 检查是否有题目
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
