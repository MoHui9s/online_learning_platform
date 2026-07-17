"""HTTP Range 视频流（对齐决策 3：MVP 用 HTTP Range 字节流，不做 HLS）。"""
import os
import re
from typing import Iterator

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse

RANGE_PATTERN = re.compile(r"bytes=(\d*)-(\d*)")


def _parse_range(range_header: str, file_size: int) -> tuple[int, int]:
    """解析 Range header，返回 (start, end) 闭区间。"""
    match = RANGE_PATTERN.search(range_header)
    if not match:
        raise HTTPException(status_code=416, detail="Range header 格式非法")

    start_str, end_str = match.groups()
    start = int(start_str) if start_str else 0
    end = int(end_str) if end_str else file_size - 1

    if start >= file_size or end >= file_size:
        raise HTTPException(
            status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            detail=f"Range {start}-{end} 超出文件大小 {file_size}",
        )
    if start > end:
        raise HTTPException(status_code=416, detail="非法 Range: start > end")

    return start, end


def _file_reader(path: str, start: int, end: int, chunk_size: int = 1024 * 1024) -> Iterator[bytes]:
    """按 chunk 逐块读取文件指定区间。"""
    with open(path, "rb") as f:
        f.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            read_size = min(chunk_size, remaining)
            data = f.read(read_size)
            if not data:
                break
            yield data
            remaining -= len(data)


def range_stream_response(file_path: str, request: Request) -> Response:
    """根据 Range header 返回 206 或完整文件。"""
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")

    if range_header is None:
        # 无 Range → 返回完整文件
        return StreamingResponse(
            _file_reader(file_path, 0, file_size - 1),
            status_code=200,
            media_type="video/mp4",
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(file_size),
            },
        )

    start, end = _parse_range(range_header, file_size)
    content_length = end - start + 1

    return StreamingResponse(
        _file_reader(file_path, start, end),
        status_code=status.HTTP_206_PARTIAL_CONTENT,
        media_type="video/mp4",
        headers={
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
        },
    )
