"""课件上传与视频流（对齐决策 3：视频走 HTTP Range）。"""
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.courseware import Courseware, CoursewareType
from app.models.user import User
from app.schemas.common import success
from app.schemas.courseware import CoursewareOut
from app.utils.file_upload import build_storage_path, save_upload, validate_file
from app.utils.video_stream import range_stream_response

router = APIRouter(prefix="/courseware", tags=["courseware"])


@router.post("/upload")
async def upload_courseware(
    chapter_id: int,
    title: str,
    file: UploadFile,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """上传课件（视频/PDF/PPT/DOC）。"""
    category, ext = validate_file(file)

    # 映射 category 到 CoursewareType
    type_map = {
        "video": CoursewareType.video,
        "pdf": CoursewareType.pdf,
        "ppt": CoursewareType.ppt,
        "doc": CoursewareType.doc,
    }

    # 构建存储路径（需要 chapter → course，先假设 course_id 通过参数或查 chapter 获取）
    dest_path = build_storage_path(settings.UPLOAD_DIR, 0, chapter_id, ext)
    file_size = await save_upload(file, dest_path)

    courseware = Courseware(
        chapter_id=chapter_id,
        title=title,
        type=type_map[category],
        file_path=dest_path,
        file_name=file.filename,
        file_size=file_size,
        mime_type=file.content_type,
        uploaded_by=current.id,
    )
    db.add(courseware)
    db.commit()
    db.refresh(courseware)

    return success(CoursewareOut.model_validate(courseware).model_dump(), message="上传成功")


@router.get("")
def list_courseware(
    chapter_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """按章节列课件。"""
    items = db.execute(
        select(Courseware)
        .where(Courseware.chapter_id == chapter_id)
        .order_by(Courseware.sort_order)
    ).scalars().all()
    return success(
        [CoursewareOut.model_validate(c).model_dump() for c in items]
    )


@router.get("/{courseware_id}")
def get_courseware(
    courseware_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """课件详情。"""
    cw = db.execute(
        select(Courseware).where(Courseware.id == courseware_id)
    ).scalar_one_or_none()
    if not cw:
        raise HTTPException(status_code=404, detail="课件不存在")
    return success(CoursewareOut.model_validate(cw).model_dump())


@router.delete("/{courseware_id}")
def delete_courseware(
    courseware_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """删除课件（仅教师/admin 或上传者本人）。"""
    cw = db.execute(
        select(Courseware).where(Courseware.id == courseware_id)
    ).scalar_one_or_none()
    if not cw:
        raise HTTPException(status_code=404, detail="课件不存在")

    # 删除磁盘文件
    import os

    if os.path.isfile(cw.file_path):
        os.remove(cw.file_path)

    db.delete(cw)
    db.commit()
    return success(message="已删除")


@router.get("/{courseware_id}/stream")
def stream_video(
    courseware_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """视频流播放（支持 Range 断点续播）。"""
    cw = db.execute(
        select(Courseware).where(Courseware.id == courseware_id)
    ).scalar_one_or_none()
    if not cw:
        raise HTTPException(status_code=404, detail="课件不存在")
    if cw.type != CoursewareType.video:
        raise HTTPException(status_code=400, detail="非视频课件，不支持流播放")

    return range_stream_response(cw.file_path, request)
