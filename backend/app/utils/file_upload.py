"""文件上传工具：类型校验、按日期分目录安全保存。"""
import os
import uuid
from datetime import date

from fastapi import HTTPException, UploadFile

from app.core.config import settings

# 允许的文件扩展名白名单：扩展名 → 类别
ALLOWED_EXTENSIONS = {
    "video": {".mp4", ".avi", ".mkv", ".mov", ".webm"},
    "pdf": {".pdf"},
    "ppt": {".ppt", ".pptx"},
    "doc": {".doc", ".docx"},
}

# 允许的 MIME 类型白名单：MIME → 类别（与扩展名双重校验）
ALLOWED_MIMETYPES = {
    "video/mp4": "video",
    "application/pdf": "pdf",
    "application/vnd.ms-powerpoint": "ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "ppt",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "doc",
}

# 单文件大小上限（按类别）
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB（视频）
MAX_DOC_SIZE = 50 * 1024 * 1024  # 50 MB（文档）


def _get_ext(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def _max_size_for(category: str) -> int:
    return MAX_FILE_SIZE if category == "video" else MAX_DOC_SIZE


def validate_file(file: UploadFile) -> tuple[str, str]:
    """校验上传文件类型与大小，返回 (类型 category, 扩展名)。

    类型 category: "video" / "pdf" / "ppt" / "doc"
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = _get_ext(file.filename)
    category = None
    for cat, exts in ALLOWED_EXTENSIONS.items():
        if ext in exts:
            category = cat
            break

    if category is None:
        allowed = ", ".join(sorted(set().union(*ALLOWED_EXTENSIONS.values())))
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 {ext}，允许: {allowed}",
        )

    # MIME 与扩展名双重校验（浏览器未知 MIME 时放行，以扩展名为准）
    mime = file.content_type or ""
    if mime in ALLOWED_MIMETYPES and ALLOWED_MIMETYPES[mime] != category:
        raise HTTPException(status_code=400, detail="文件类型与内容不匹配")

    # 根据类型设置大小上限（不加载全文件到内存）
    max_size = _max_size_for(category)
    if file.size and file.size > max_size:
        limit_mb = max_size / 1024 / 1024
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({limit_mb:.0f} MB)",
        )

    return category, ext


async def save_upload(file: UploadFile) -> dict:
    """校验并保存上传文件到 UPLOAD_DIR（按日期分目录），返回文件元信息 dict。"""
    category, ext = validate_file(file)
    max_size = _max_size_for(category)
    mime = file.content_type or "application/octet-stream"

    # 创建按日分子目录
    subdir = os.path.join(settings.UPLOAD_DIR, date.today().isoformat())
    os.makedirs(subdir, exist_ok=True)

    stored_name = f"{uuid.uuid4().hex}{ext}"
    full_path = os.path.join(subdir, stored_name)

    # 流式写入磁盘，边写边校验大小兜底（file.size 可能缺失）
    size = 0
    with open(full_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > max_size:
                f.close()
                os.remove(full_path)
                limit_mb = max_size / 1024 / 1024
                raise HTTPException(
                    status_code=413,
                    detail=f"文件大小超过限制 ({limit_mb:.0f} MB)",
                )
            f.write(chunk)

    # 相对路径（相对于 UPLOAD_DIR）
    relative_path = os.path.join(date.today().isoformat(), stored_name)

    return {
        "file_path": relative_path,
        "file_name": file.filename,
        "file_size": size,
        "mime_type": mime,
    }
