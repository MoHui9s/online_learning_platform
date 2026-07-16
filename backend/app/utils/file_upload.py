"""文件上传工具：保存上传文件到 UPLOAD_DIR，按日期分目录避免单目录文件堆积。"""
import os
import uuid
from datetime import date

from fastapi import HTTPException, UploadFile

from app.core.config import settings

# 允许的课件 MIME 类型
ALLOWED_MIMETYPES = {    #todo
    "video/mp4": "video",
    "application/pdf": "pdf",
    "application/vnd.ms-powerpoint": "ppt",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "ppt",
    "application/msword": "doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "doc",
    "video": {".mp4", ".avi", ".mkv", ".mov", ".webm"},
    "pdf": {".pdf"},
    "ppt": {".ppt", ".pptx"},
    "doc": {".doc", ".docx"},      
}

MAX_UPLOAD_SIZE = 200 * 1024 * 1024  # 200 MB   #todo
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB（视频）#todo
MAX_DOC_SIZE = 50 * 1024 * 1024  # 50 MB（文档）    #todo


async def save_upload(file: UploadFile) -> dict:
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
        while chunk := await file.file.read(1024 * 1024):
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

def _get_ext(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


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
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型 {ext}，允许: {', '.join(sum(ALLOWED_EXTENSIONS.values(), set()))}",
        )

    # 根据类型设置大小上限
    max_size = MAX_FILE_SIZE if category == "video" else MAX_DOC_SIZE   #todo

    # 尝试读一小段检查大小（不加载全文件到内存）
    if file.size and file.size > max_size:
        limit_mb = max_size / 1024 / 1024
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制 ({limit_mb:.0f} MB)",
        )

    return category, ext

def build_storage_path(upload_dir: str, course_id: int, chapter_id: int, ext: str) -> str:
    """构建文件存储路径: UPLOAD_DIR/course_{id}/chapter_{id}/{uuid}.{ext}"""
    relative = os.path.join("course_" + str(course_id), "chapter_" + str(chapter_id))
    full_dir = os.path.join(upload_dir, relative)
    os.makedirs(full_dir, exist_ok=True)
    filename = str(uuid.uuid4()) + ext
    return os.path.join(full_dir, filename)
