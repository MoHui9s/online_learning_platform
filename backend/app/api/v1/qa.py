"""C4: RAG 智能答疑路由。"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.qa_history import QAHistory
from app.models.user import User
from app.schemas.common import paginate, success
from app.schemas.qa import QAAskRequest, QAHistoryOut, KnowledgeBaseBuildRequest
from app.services.rag_service import build_knowledge_base, rag_query_stream

router = APIRouter(tags=["qa"])


@router.post("/courses/{course_id}/knowledge-base/build")
def build_kb(
    course_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """触发知识库构建：解析课件→切块→向量化→存 ChromaDB。

    异步后台执行（BackgroundTasks，对齐决策2）。
    """
    # 权限检查
    from app.models.user import UserRole

    if current.role not in (UserRole.teacher, UserRole.admin):
        raise HTTPException(status_code=403, detail="仅教师/管理员可构建知识库")

    background_tasks.add_task(build_knowledge_base, course_id)
    return success(message="知识库构建任务已提交，后台处理中")


@router.post("/qa/ask")
async def ask_qa(
    payload: QAAskRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """流式问答（SSE text/event-stream）。

    检索 ChromaDB → 拼 prompt → LLM 流式生成 → SSE 推送。
    """
    async def event_stream():
        full_answer = ""
        try:
            async for token in rag_query_stream(payload.course_id, payload.question):
                full_answer += token
                yield token
        except NotImplementedError:
            pass  # 骨架阶段已 yield 占位消息

        # 写问答历史
        try:
            qa = QAHistory(
                user_id=current.id,
                course_id=payload.course_id,
                question=payload.question,
                answer=full_answer if full_answer else None,
            )
            db.add(qa)
            db.commit()
        except Exception:
            pass  # 记录失败不影响主流程

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/qa/history")
def qa_history(
    course_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """问答历史分页查询，按课程筛选。"""
    stmt = select(QAHistory).where(QAHistory.user_id == current.id)
    count_stmt = select(QAHistory.id).where(QAHistory.user_id == current.id)

    if course_id:
        stmt = stmt.where(QAHistory.course_id == course_id)
        count_stmt = count_stmt.where(QAHistory.course_id == course_id)

    total = len(db.execute(count_stmt).scalars().all())
    items = db.execute(
        stmt.order_by(QAHistory.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    return success(
        paginate(
            [QAHistoryOut.model_validate(r).model_dump() for r in items],
            total,
            page,
            page_size,
        )
    )
