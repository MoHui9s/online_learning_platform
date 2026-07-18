from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select, text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.course import Course, CourseStatus
from app.models.learning import LearningRecord
from app.models.user import User, UserRole
from app.schemas.common import success

router = APIRouter(prefix="/stats", tags=["stats"])


def _build_progress_cases():
    """Build CASE WHEN clauses to bucket progress into 5 ranges."""
    return [
        (LearningRecord.progress < 20, "0-20%"),
        ((LearningRecord.progress >= 20) & (LearningRecord.progress < 40), "20-40%"),
        ((LearningRecord.progress >= 40) & (LearningRecord.progress < 60), "40-60%"),
        ((LearningRecord.progress >= 60) & (LearningRecord.progress < 80), "60-80%"),
        (LearningRecord.progress >= 80, "80-100%"),
    ]


@router.get("")
def get_stats(_: object = Depends(get_current_user), db: Session = Depends(get_db)):
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)

    # ── summary KPIs ──
    student_count = db.execute(
        select(func.count())
        .select_from(User)
        .where(User.role == UserRole.student)
        .where(User.is_active == True)
    ).scalar_one()

    course_count = db.execute(
        select(func.count())
        .select_from(Course)
        .where(Course.status == CourseStatus.published)
    ).scalar_one()

    today_active = db.execute(
        select(func.count(func.distinct(LearningRecord.user_id)))
        .where(LearningRecord.updated_at >= today_start)
    ).scalar_one()

    summary = [
        {"label": "学习人数", "value": student_count},
        {"label": "课程总数", "value": course_count},
        {"label": "今日活跃", "value": today_active},
    ]

    # ── daily active trend (last 7 days) ──
    seven_days_ago = today_start - timedelta(days=6)
    daily_rows = (
        db.execute(
            select(
                func.date(LearningRecord.updated_at).label("day"),
                func.count(func.distinct(LearningRecord.user_id)).label("cnt"),
            )
            .where(LearningRecord.updated_at >= seven_days_ago)
            .group_by(text("day"))
            .order_by(text("day"))
        )
        .mappings()
        .all()
    )

    # fill missing dates with 0
    daily_map = {row["day"].isoformat() if hasattr(row["day"], "isoformat") else str(row["day"]): row["cnt"] for row in daily_rows}
    daily_active_trend = []
    for i in range(7):
        d = (today - timedelta(days=6 - i)).isoformat()
        daily_active_trend.append({"date": d, "count": daily_map.get(d, 0)})

    # ── course enrollment (top 10 by distinct learners) ──
    course_rows = (
        db.execute(
            select(
                Course.title.label("name"),
                func.count(func.distinct(LearningRecord.user_id)).label("count"),
            )
            .select_from(LearningRecord)
            .join(Course, LearningRecord.course_id == Course.id)
            .group_by(Course.id, Course.title)
            .order_by(text("count DESC"))
            .limit(10)
        )
        .mappings()
        .all()
    )
    course_enrollment = [{"name": row["name"], "count": row["count"]} for row in course_rows]

    # ── progress distribution (5 buckets) ──
    progress_case = case(*[(cond, label) for cond, label in _build_progress_cases()], else_="other")
    progress_rows = (
        db.execute(
            select(
                progress_case.label("range"),
                func.count().label("count"),
            )
            .select_from(LearningRecord)
            .group_by(text("`range`"))
            .order_by(text("`range`"))
        )
        .mappings()
        .all()
    )
    # ensure all 5 buckets present
    all_ranges = ["0-20%", "20-40%", "40-60%", "60-80%", "80-100%"]
    progress_map = {row["range"]: row["count"] for row in progress_rows}
    progress_distribution = [{"range": r, "count": progress_map.get(r, 0)} for r in all_ranges]

    return success(
        {
            "summary": summary,
            "daily_active_trend": daily_active_trend,
            "course_enrollment": course_enrollment,
            "progress_distribution": progress_distribution,
        }
    )
