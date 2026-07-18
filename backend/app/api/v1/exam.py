from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.exam import Exam, ExamSubmission, SubmissionStatus
from app.models.exam_question import ExamQuestion, QuestionType
from app.schemas.common import paginate, success
from app.schemas.exam import (
    ExamDetailOut,
    ExamOut,
    ExamQuestionOut,
    ExamSubmissionOut,
    ExamSubmissionIn,
)

router = APIRouter(prefix="/exams", tags=["exams"])


@router.get("")
def list_exams(
    page: int = 1,
    page_size: int = 20,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Exam).options(selectinload(Exam.course))
    total = db.execute(select(func.count()).select_from(Exam)).scalar_one()
    items = db.execute(query.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    payload = []
    for item in items:
        item_data = ExamOut.model_validate(item).model_dump()
        item_data["course_name"] = item.course.title if item.course else None
        submission = db.execute(
            select(ExamSubmission)
            .where(ExamSubmission.exam_id == item.id)
            .where(ExamSubmission.user_id == current_user.id)
        ).scalar_one_or_none()
        item_data["submitted"] = submission is not None
        item_data["submission_status"] = submission.status.value if submission else None
        item_data["answers"] = submission.answers if submission else ''
        item_data["score"] = submission.score if submission else None
        payload.append(item_data)
    return success(
        paginate(payload, total, page, page_size)
    )


@router.get("/{exam_id}")
def get_exam_detail(
    exam_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exam = db.execute(
        select(Exam)
        .where(Exam.id == exam_id)
        .options(selectinload(Exam.course), selectinload(Exam.questions))
    ).scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    questions = [q for q in exam.questions]
    payload = {
        **ExamOut.model_validate(exam).model_dump(),
        "course_name": exam.course.title if exam.course else None,
        "questions": [
            {
                "id": q.id,
                "exam_id": q.exam_id,
                "question": q.question,
                "question_type": q.question_type.value if q.question_type else None,
                "options": q.options,
                "score": q.score,
                "created_at": q.created_at,
                "updated_at": q.updated_at,
            }
            for q in questions
        ],
    }

    submission = db.execute(
        select(ExamSubmission)
        .where(ExamSubmission.exam_id == exam.id)
        .where(ExamSubmission.user_id == current_user.id)
    ).scalar_one_or_none()
    payload["submitted"] = submission is not None
    payload["submission_status"] = submission.status.value if submission else None
    payload["answers"] = submission.answers if submission else ""

    return success(ExamDetailOut.model_validate(payload).model_dump())


def _normalize_answers(answers):
    if answers is None:
        return {}
    if isinstance(answers, str):
        try:
            return json.loads(answers)
        except json.JSONDecodeError:
            return {"text": answers}
    if isinstance(answers, dict):
        return answers
    return {str(i): value for i, value in enumerate(answers)}


def _parse_answer_value(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


def _evaluate_question_answer(question: ExamQuestion, answer_value):
    if answer_value is None:
        return 0

    correct = _parse_answer_value(question.correct_answer) if question.correct_answer is not None else None
    if correct is None:
        return 0

    qtype = question.question_type.value if hasattr(question.question_type, 'value') else str(question.question_type)
    if qtype in (QuestionType.single.value, QuestionType.text.value):
        return 1 if str(answer_value).strip().lower() == str(correct).strip().lower() else 0

    if qtype == QuestionType.multiple.value:
        if isinstance(answer_value, list):
            submitted_set = {str(item).strip().lower() for item in answer_value}
        else:
            submitted_set = {str(answer_value).strip().lower()}
        if isinstance(correct, list):
            correct_set = {str(item).strip().lower() for item in correct}
        else:
            correct_set = {str(correct).strip().lower()}
        return 1 if submitted_set == correct_set else 0

    return 0


@router.post("/{exam_id}/submit")
def submit_exam(
    exam_id: int,
    payload: ExamSubmissionIn,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    exam = db.execute(select(Exam).where(Exam.id == exam_id)).scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    questions = db.execute(select(ExamQuestion).where(ExamQuestion.exam_id == exam_id)).scalars().all()
    normalized_answers = _normalize_answers(payload.answers)

    score = 0
    graded = True
    for question in questions:
        answer_value = normalized_answers.get(str(question.id))
        if question.correct_answer is None:
            graded = False
            continue
        correct_score = _evaluate_question_answer(question, answer_value)
        score += question.score if correct_score else 0

    status = SubmissionStatus.graded if graded else SubmissionStatus.pending
    answers_payload = json.dumps(normalized_answers, ensure_ascii=False)

    existing = db.execute(
        select(ExamSubmission)
        .where(ExamSubmission.exam_id == exam.id)
        .where(ExamSubmission.user_id == current_user.id)
    ).scalar_one_or_none()
    if existing:
        existing.answers = answers_payload
        existing.score = score
        existing.submitted_at = datetime.utcnow()
        existing.status = status
        db.add(existing)
        db.commit()
        db.refresh(existing)
        submission = existing
    else:
        submission = ExamSubmission(
            exam_id=exam.id,
            user_id=current_user.id,
            answers=answers_payload,
            score=score,
            status=status,
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)

    return success(ExamSubmissionOut.model_validate(submission).model_dump(), message="考试提交成功")
