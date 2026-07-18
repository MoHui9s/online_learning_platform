"""课件路由：上传 / 更新 / 删除（配合 multipart 文件上传）。"""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.chapter import Chapter
from app.models.courseware import Courseware
from app.models.user import User
from app.schemas.common import success
from app.schemas.course import CoursewareCreate, CoursewareOut, CoursewareUpdate

router = APIRouter(prefix="/chapters", tags=["coursewares"])

ALLOWED_EXTENSIONS = {".mp4", ".pdf", ".ppt", ".pptx", ".doc", ".docx", ".txt", ".zip", ".rar", ".jpg", ".png"}
UPLOAD_SUBDIR = "courseware"


def _save_upload(file: UploadFile) -> tuple[str, str, int]:
    """保存上传文件到本地，返回 (file_path, file_name, file_size)。"""
    ext = Path(file.filename or "file").suffix.lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    dest_dir = Path(settings.UPLOAD_DIR) / UPLOAD_SUBDIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / safe_name

    size = 0
    with open(dest_path, "wb") as f:
        # 逐块写入避免大文件占满内存
        while chunk := file.file.read(1024 * 1024):
            f.write(chunk)
            size += len(chunk)

    relative = f"/uploads/{UPLOAD_SUBDIR}/{safe_name}"
    return relative, file.filename or safe_name, size


# ── 创建课件（带文件上传）────────────────────────────

@router.post("/{chapter_id}/coursewares", status_code=201)
def create_courseware(
    chapter_id: int,
    title: str = Form(..., min_length=1, max_length=200),
    type: str = Form(..., min_length=1, max_length=50),
    sort_order: int = Form(0),
    file: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    chapter = db.execute(
        select(Chapter).where(Chapter.id == chapter_id)
    ).scalar_one_or_none()
    if not chapter:
        raise HTTPException(status_code=404, detail="章节不存在")

    file_path = ""
    file_name = None
    file_size = None
    mime_type = None

    if file and file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")
        file_path, file_name, file_size = _save_upload(file)
        mime_type = file.content_type

    # 无文件且路径未提供 → 报错
    if not file_path:
        raise HTTPException(status_code=400, detail="请上传文件")

    courseware = Courseware(
        chapter_id=chapter_id,
        title=title,
        type=type,
        file_path=file_path,
        file_name=file_name,
        file_size=file_size,
        mime_type=mime_type,
        sort_order=sort_order,
        uploaded_by=current_user.id,
    )
    db.add(courseware)
    db.commit()
    db.refresh(courseware)
    return success(CoursewareOut.model_validate(courseware).model_dump(), message="课件已创建")


# ── 更新课件（可选换文件）────────────────────────────

@router.put("/{chapter_id}/coursewares/{courseware_id}")
def update_courseware(
    chapter_id: int,
    courseware_id: int,
    title: str | None = Form(None, min_length=1, max_length=200),
    sort_order: int | None = Form(None),
    file: UploadFile | None = File(None),
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    courseware = db.execute(
        select(Courseware).where(
            Courseware.id == courseware_id,
            Courseware.chapter_id == chapter_id,
        )
    ).scalar_one_or_none()
    if not courseware:
        raise HTTPException(status_code=404, detail="课件不存在")

    updated = False
    if title is not None:
        courseware.title = title
        updated = True
    if sort_order is not None:
        courseware.sort_order = sort_order
        updated = True

    if file and file.filename:
        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")
        file_path, file_name, file_size = _save_upload(file)
        courseware.file_path = file_path
        courseware.file_name = file_name
        courseware.file_size = file_size
        courseware.mime_type = file.content_type
        updated = True

    if not updated:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")

    db.add(courseware)
    db.commit()
    db.refresh(courseware)
    return success(CoursewareOut.model_validate(courseware).model_dump(), message="课件已更新")


# ── 删除课件 ────────────────────────────────────────

@router.delete("/{chapter_id}/coursewares/{courseware_id}")
def delete_courseware(
    chapter_id: int,
    courseware_id: int,
    _: object = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    courseware = db.execute(
        select(Courseware).where(
            Courseware.id == courseware_id,
            Courseware.chapter_id == chapter_id,
        )
    ).scalar_one_or_none()
    if not courseware:
        raise HTTPException(status_code=404, detail="课件不存在")

    # 删除物理文件（忽略文件不存在的情况）
    if courseware.file_path:
        abs_path = Path(settings.UPLOAD_DIR) / courseware.file_path.lstrip("/uploads/").replace("/", os.sep)
        try:
            abs_path.unlink(missing_ok=True)
        except OSError:
            pass

    db.delete(courseware)
    db.commit()
    return success(message="课件已删除")
