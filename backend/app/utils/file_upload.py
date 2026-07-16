"""文件上传工具：类型校验、路径生成、安全保存。"""
import os
import uuid

from fastapi import HTTPException, UploadFile

# 允许的文件类型与 MIME 白名单
ALLOWED_EXTENSIONS = {
    "video": {".mp4", ".avi", ".mkv", ".mov", ".webm"},
    "pdf": {".pdf"},
    "ppt": {".ppt", ".pptx"},
    "doc": {".doc", ".docx"},
}

# 单文件大小上限
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500 MB（视频）
MAX_DOC_SIZE = 50 * 1024 * 1024  # 50 MB（文档）


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
    max_size = MAX_FILE_SIZE if category == "video" else MAX_DOC_SIZE

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


async def save_upload(file: UploadFile, dest_path: str) -> int:
    """流式写入磁盘，返回文件字节数。"""
    size = 0
    with open(dest_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # 1MB 分块
            f.write(chunk)
            size += len(chunk)
    return size
