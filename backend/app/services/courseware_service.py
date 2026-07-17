"""课件 Service：课件 CRUD + 文件上传。"""
import os

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.courseware import Courseware, CoursewareType
from app.services.chapter_service import get_by_id as get_chapter
from app.utils.file_upload import save_upload


def get_list(db: Session, chapter_id: int) -> list[Courseware]:
    return list(
        db.execute(
            select(Courseware)
            .where(Courseware.chapter_id == chapter_id)
            .order_by(Courseware.sort_order)
        ).scalars().all()
    )


def get_by_id(db: Session, courseware_id: int) -> Courseware:
    cw = db.get(Courseware, courseware_id)
    if not cw:
        raise HTTPException(status_code=404, detail="课件不存在")
    return cw


async def upload(
    db: Session,
    chapter_id: int,
    file: UploadFile,
    title: str,
    cw_type: CoursewareType,
    sort_order: int,
    uploaded_by: int,
) -> Courseware:
    get_chapter(db, chapter_id)  # 校验章节存在

    file_info = await save_upload(file)

    # 视频取时长（简单从文件名判断，或后续集成 ffprobe）
    duration = None
    if cw_type == CoursewareType.video:
        duration = 0  # MVP 暂不入库精确时长

    cw = Courseware(
        chapter_id=chapter_id,
        title=title,
        type=cw_type,
        file_path=file_info["file_path"],
        file_name=file_info["file_name"],
        file_size=file_info["file_size"],
        mime_type=file_info["mime_type"],
        duration=duration,
        sort_order=sort_order,
        uploaded_by=uploaded_by,
    )
    db.add(cw)
    db.commit()
    db.refresh(cw)
    return cw


def update_courseware(
    db: Session,
    courseware_id: int,
    title: str | None,
    sort_order: int | None,
) -> Courseware:
    cw = get_by_id(db, courseware_id)
    if title is not None:
        cw.title = title
    if sort_order is not None:
        cw.sort_order = sort_order
    db.commit()
    db.refresh(cw)
    return cw


def delete_courseware(db: Session, courseware_id: int) -> None:
    cw = get_by_id(db, courseware_id)
    # 删除物理文件
    full_path = os.path.join(settings.UPLOAD_DIR, cw.file_path)
    if os.path.exists(full_path):
        os.remove(full_path)
    db.delete(cw)
    db.commit()
