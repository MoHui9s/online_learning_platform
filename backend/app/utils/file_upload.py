"""文件上传工具：保存上传文件到 UPLOAD_DIR，按日期分目录避免单目录文件堆积。"""
import os
import uuid
from datetime import date

from fastapi import HTTPException, UploadFile

from app.core.config import settings

# 允许的课件 MIME 类型
ALLOWED_MIMETYPES = {
    "video/mp4": "video",
    "application/pdf": "pdf",
    "application/vnd.ms-powerpoint": "ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "ppt",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "doc",
}

MAX_UPLOAD_SIZE = 200 * 1024 * 1024  # 200 MB


def save_upload(file: UploadFile) -> dict:
    """保存上传文件，返回文件元信息 dict。"""
    mime = file.content_type or "application/octet-stream"
    ext = _ext_from_filename(file.filename or "file.bin")

    # 创建按日分子目录
    subdir = os.path.join(settings.UPLOAD_DIR, date.today().isoformat())
    os.makedirs(subdir, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}{ext}"
    full_path = os.path.join(subdir, stored_name)

    # 流式写入磁盘
    size = 0
    with open(full_path, "wb") as f:
        while chunk := file.file.read(8192):
            size += len(chunk)
            if size > MAX_UPLOAD_SIZE:
                os.remove(full_path)
                raise HTTPException(status_code=413, detail="文件超过 200MB 上限")
            f.write(chunk)

    # 相对路径（相对于 UPLOAD_DIR）
    relative_path = os.path.join(date.today().isoformat(), stored_name)

    return {
        "file_path": relative_path,
        "file_name": file.filename,
        "file_size": size,
        "mime_type": mime,
    }


def _ext_from_filename(filename: str) -> str:
    _, dot_ext = os.path.splitext(filename)
    if dot_ext:
        return dot_ext.lower()
    return ".bin"
