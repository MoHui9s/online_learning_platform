from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.learning import LearningRecord
from app.schemas.common import paginate, success
from app.schemas.learning import LearningProgressIn, LearningRecordOut

router = APIRouter(prefix="/learning", tags=["learning"])


@router.get("")
def list_learning_records(
    page: int = 1,
    page_size: int = 20,
    course_id: int | None = None,
    chapter_id: int | None = None,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        select(LearningRecord)
        .where(LearningRecord.user_id == current_user.id)
        .options(
            selectinload(LearningRecord.course),
            selectinload(LearningRecord.chapter),
        )
    )
    if course_id is not None:
        query = query.where(LearningRecord.course_id == course_id)
    if chapter_id is not None:
        query = query.where(LearningRecord.chapter_id == chapter_id)

    total = db.execute(
        select(func.count()).select_from(query.subquery())
    ).scalar_one()
    items = db.execute(query.order_by(LearningRecord.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)).scalars().all()
    payload = []
    for item in items:
        item_data = LearningRecordOut.model_validate(item).model_dump()
        item_data["course_title"] = item.course.title if item.course else None
        item_data["chapter_title"] = item.chapter.title if item.chapter else None
        payload.append(item_data)
    return success(paginate(payload, total, page, page_size))


@router.post("/progress")
def report_progress(
    payload: LearningProgressIn,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = (
        db.execute(
            select(LearningRecord)
            .where(LearningRecord.user_id == current_user.id)
            .where(LearningRecord.course_id == payload.course_id)
            .where(LearningRecord.chapter_id == payload.chapter_id)
        )
        .scalar_one_or_none()
    )
    if not record:
        record = LearningRecord(
            user_id=current_user.id,
            course_id=payload.course_id,
            chapter_id=payload.chapter_id,
            progress=payload.progress,
        )
        db.add(record)
    else:
        record.progress = max(record.progress, int(payload.progress))
    db.commit()
    db.refresh(record)
    return success(LearningRecordOut.model_validate(record).model_dump())
