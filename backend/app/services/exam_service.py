"""考试业务逻辑：自动阅卷、错题沉淀、组卷。"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.exam import Exam, ExamRecord, ExamRecordStatus, WrongQuestion
from app.models.question import Question, QuestionType


def auto_grade(question: Question, user_answer: dict) -> float | None:
    """自动阅卷：客观题返回得分，主观题返回 None（需人工批阅）。"""
    if question.type == QuestionType.short_answer:
        return None  # 简答题需人工批阅

    correct = question.answer
    # 单选/判断/多选：correct = {"keys": ["A"]} 或 {"keys": ["B","C"]}
    user_keys = set(user_answer.get("keys", []))
    correct_keys = set(correct.get("keys", []))

    if not correct_keys:
        return None  # 答案格式异常

    if question.type in (QuestionType.single, QuestionType.judge):
        # 单选/判断：完全匹配
        return float(question.score) if user_keys == correct_keys else 0.0
    elif question.type == QuestionType.multiple:
        # 多选：完全匹配才得分
        return float(question.score) if user_keys == correct_keys else 0.0

    return None


def grade_and_persist(
    db: Session, record: ExamRecord, answers: dict[int, dict]
) -> float:
    """批阅整卷：遍历每题判分 + 写错题本，返回总分。"""
    exam = db.execute(
        select(Exam).where(Exam.id == record.exam_id)
    ).scalar_one()
    total = 0.0

    # 获取考试关联的题目（含分值）
    from app.models.exam import ExamQuestion

    eq_list = db.execute(
        select(ExamQuestion, Question)
        .join(Question, Question.id == ExamQuestion.question_id)
        .where(ExamQuestion.exam_id == exam.id)
    ).all()

    for eq, question in eq_list:
        user_answer = answers.get(str(question.id))
        if user_answer is None:
            continue  # 未作答

        score = auto_grade(question, user_answer)

        if score is not None:
            if score == 0:
                # 答错了 → 错题本
                _upsert_wrong(db, record.user_id, question.id, record.id, user_answer)
            total += score

    # 更新记录
    record.score = total
    record.status = ExamRecordStatus.graded
    record.submitted_at = datetime.now(timezone.utc)
    db.commit()

    return total


def _upsert_wrong(
    db: Session,
    user_id: int,
    question_id: int,
    exam_record_id: int,
    wrong_answer: dict,
) -> None:
    """写入/更新错题本。"""
    existing = db.execute(
        select(WrongQuestion).where(
            WrongQuestion.user_id == user_id,
            WrongQuestion.question_id == question_id,
        )
    ).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if existing:
        existing.wrong_answer = wrong_answer
        existing.wrong_count += 1
        existing.last_wrong_at = now
        existing.is_mastered = False
    else:
        db.add(
            WrongQuestion(
                user_id=user_id,
                question_id=question_id,
                exam_record_id=exam_record_id,
                wrong_answer=wrong_answer,
                wrong_count=1,
                last_wrong_at=now,
            )
        )
    db.flush()
