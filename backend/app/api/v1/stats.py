"""C6: 学习分析统计路由。

读端模块，纯消费 BE-B/C2/C3 产出的数据，不写库。
"""
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.exam import Exam, ExamRecord, ExamRecordStatus, WrongQuestion
from app.models.knowledge_point import KnowledgePoint
from app.models.question import Question, QuestionKnowledgePoint
from app.models.enrollment import Enrollment
from app.models.learning_calendar import LearningCalendar
from app.models.learning_record import LearningRecord
from app.models.user import User
from app.schemas.common import success
from app.schemas.qa import (
    CalendarDay,
    CourseOverview,
    DurationTrend,
    ExamScoreDistribution,
    ExamStats,
    KnowledgeMastery,
)

router = APIRouter(tags=["stats"])


# ===================== 学习日历热力图 =====================


@router.get("/stats/calendar")
def stats_calendar(
    year: int = Query(...),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """学习日历热力图数据：指定月份每日学习时长/课件数。"""
    rows = db.execute(
        select(LearningCalendar).where(
            LearningCalendar.user_id == current.id,
            func.extract("year", LearningCalendar.study_date) == year,
            func.extract("month", LearningCalendar.study_date) == month,
        )
    ).scalars().all()

    days = [
        CalendarDay(
            date=str(r.study_date),
            duration_minutes=r.duration_seconds // 60,
            courseware_count=r.courseware_count,
            note_count=r.note_count,
        )
        for r in rows
    ]

    return success([d.model_dump() for d in days])


# ===================== 学习时长趋势 =====================


@router.get("/stats/duration")
def stats_duration(
    period: str = Query("week", pattern="^(day|week|month)$"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """学习时长趋势：按日/周聚合，供 ECharts。"""
    from datetime import date, timedelta

    end = func.current_date()
    start = end - timedelta(days=days)

    if period == "day":
        rows = (
            db.execute(
                select(LearningCalendar.study_date, func.sum(LearningCalendar.duration_seconds))
                .where(
                    LearningCalendar.user_id == current.id,
                    LearningCalendar.study_date >= start,
                )
                .group_by(LearningCalendar.study_date)
                .order_by(LearningCalendar.study_date)
            )
            .all()
        )
    elif period == "week":
        rows = (
            db.execute(
                select(
                    func.date_format(LearningCalendar.study_date, "%Y-%u"),
                    func.sum(LearningCalendar.duration_seconds),
                )
                .where(
                    LearningCalendar.user_id == current.id,
                    LearningCalendar.study_date >= start,
                )
                .group_by(func.date_format(LearningCalendar.study_date, "%Y-%u"))
                .order_by("1")
            )
            .all()
        )
    else:  # month
        rows = (
            db.execute(
                select(
                    func.date_format(LearningCalendar.study_date, "%Y-%m"),
                    func.sum(LearningCalendar.duration_seconds),
                )
                .where(
                    LearningCalendar.user_id == current.id,
                    LearningCalendar.study_date >= start,
                )
                .group_by(func.date_format(LearningCalendar.study_date, "%Y-%m"))
                .order_by("1")
            )
            .all()
        )

    trends = [
        DurationTrend(period=str(p), total_minutes=(s or 0) // 60).model_dump()
        for p, s in rows
    ]
    return success(trends)


# ===================== 知识点掌握度 =====================


@router.get("/stats/knowledge-mastery")
def stats_knowledge_mastery(
    course_id: int = Query(...),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """知识点掌握度：由错题/答题记录 × question_knowledge_points 计算。"""
    # 获取课程所有知识点
    kps = db.execute(
        select(KnowledgePoint).where(KnowledgePoint.course_id == course_id)
    ).scalars().all()

    result = []
    for kp in kps:
        # 该知识点关联的题目
        qkps = db.execute(
            select(QuestionKnowledgePoint).where(
                QuestionKnowledgePoint.knowledge_point_id == kp.id
            )
        ).scalars().all()
        q_ids = [qkp.question_id for qkp in qkps]

        if not q_ids:
            result.append(
                KnowledgeMastery(
                    knowledge_point_id=kp.id,
                    knowledge_point_name=kp.name,
                ).model_dump()
            )
            continue

        total_q = len(q_ids)

        # 错题次数
        wrong_count = len(
            db.execute(
                select(WrongQuestion.id).where(
                    WrongQuestion.user_id == current.id,
                    WrongQuestion.question_id.in_(q_ids),
                    WrongQuestion.is_mastered == False,
                )
            ).scalars().all()
        )

        mastery_rate = max(0, round((1 - wrong_count / total_q) * 100, 1)) if total_q else 0

        result.append(
            KnowledgeMastery(
                knowledge_point_id=kp.id,
                knowledge_point_name=kp.name,
                total_questions=total_q,
                wrong_count=wrong_count,
                mastery_rate=mastery_rate,
            ).model_dump()
        )

    return success(result)


# ===================== 成绩分布 =====================


@router.get("/stats/exam/{exam_id}/distribution")
def stats_exam_distribution(
    exam_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """教师视角：某次考试的成绩分布。"""
    from app.models.user import UserRole

    if current.role not in (UserRole.teacher, UserRole.admin):
        raise HTTPException(status_code=403, detail="仅教师/管理员可查看")

    exam = db.get(Exam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    records = db.execute(
        select(ExamRecord).where(
            ExamRecord.exam_id == exam_id,
            ExamRecord.status.in_([ExamRecordStatus.submitted, ExamRecordStatus.graded]),
        )
    ).scalars().all()

    submitted_count = len(records)
    scores = [r.score for r in records if r.score is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    pass_count = sum(1 for s in scores if s >= exam.pass_score)
    pass_rate = round(pass_count / len(scores) * 100, 1) if scores else 0

    # 分段分布
    ranges = [("0-59", 0, 59), ("60-69", 60, 69), ("70-79", 70, 79), ("80-89", 80, 89), ("90-100", 90, 100)]
    distribution = []
    for label, lo, hi in ranges:
        distribution.append(
            ExamScoreDistribution(
                range_label=label, count=sum(1 for s in scores if lo <= s <= hi)
            ).model_dump()
        )

    stats = ExamStats(
        exam_title=exam.title,
        total_students=len(
            db.execute(select(ExamRecord.id).where(ExamRecord.exam_id == exam_id)).scalars().all()
        ),
        submitted_count=submitted_count,
        avg_score=avg_score,
        pass_rate=pass_rate,
        distribution=distribution,
    )
    return success(stats.model_dump())


# ===================== 课程概览（教师） =====================


@router.get("/stats/courses/{course_id}/overview")
def stats_course_overview(
    course_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """教师视角：课程概览（选课数/完课率/平均进度/学习总时长）。"""
    from app.models.user import UserRole

    if current.role not in (UserRole.teacher, UserRole.admin):
        raise HTTPException(status_code=403, detail="仅教师/管理员可查看")

    # 选课人数
    enrollments = db.execute(
        select(Enrollment).where(Enrollment.course_id == course_id)
    ).scalars().all()
    enrolled_count = len(enrollments)

    # 完课率
    completed = sum(1 for e in enrollments if e.progress_percent >= 100)
    completion_rate = round(completed / enrolled_count * 100, 1) if enrolled_count else 0

    # 平均进度
    avg_progress = (
        round(sum(e.progress_percent for e in enrollments) / enrolled_count, 1)
        if enrolled_count
        else 0
    )

    # 总学习时长（从 learning_records 聚合）
    total_seconds_row = (
        db.execute(
            select(func.coalesce(func.sum(LearningRecord.duration_watched), 0)).where(
                LearningRecord.course_id == course_id
            )
        ).scalar_one()
        if enrolled_count
        else 0
    )

    from app.models.course import Course

    course = db.get(Course, course_id)
    overview = CourseOverview(
        course_id=course_id,
        course_title=course.title if course else "",
        enrolled_count=enrolled_count,
        completion_rate=completion_rate,
        avg_progress=avg_progress,
        total_learning_minutes=(total_seconds_row or 0) // 60,
    )
    return success(overview.model_dump())
