"""课件路由：上传 / 列表 / 删除。"""
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_teacher
from app.models.courseware import CoursewareType
from app.models.user import User
from app.schemas.common import success
from app.schemas.courseware import CoursewareOut, CoursewareUpdate
from app.services import courseware_service

router = APIRouter(prefix="/chapters", tags=["courseware"])


@router.get("/{chapter_id}/courseware")
def list_courseware(chapter_id: int, db: Session = Depends(get_db)):
    items = courseware_service.get_list(db, chapter_id)
    return success([CoursewareOut.model_validate(cw).model_dump() for cw in items])


@router.post("/{chapter_id}/courseware")
async def upload_courseware(
    chapter_id: int,
    title: str = Form(min_length=1, max_length=200),
    type: CoursewareType = Form(),
    sort_order: int = Form(default=0),
    file: UploadFile = File(),
    current: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    cw = await courseware_service.upload(
        db, chapter_id, file, title, type, sort_order, current.id
    )
    return success(CoursewareOut.model_validate(cw).model_dump(), message="课件上传成功")


@router.put("/{chapter_id}/courseware/{courseware_id}")
def update_courseware_info(
    chapter_id: int,
    courseware_id: int,
    payload: CoursewareUpdate,
    current: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    cw = courseware_service.update_courseware(db, courseware_id, payload.title, payload.sort_order)
    return success(CoursewareOut.model_validate(cw).model_dump(), message="课件已更新")


@router.delete("/{chapter_id}/courseware/{courseware_id}")
def delete_courseware(
    chapter_id: int,
    courseware_id: int,
    current: User = Depends(require_teacher),
    db: Session = Depends(get_db),
):
    courseware_service.delete_courseware(db, courseware_id)
    return success(message="课件已删除")
