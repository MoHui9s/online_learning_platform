import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.qa import QAQuestion, QAStatus
from app.schemas.common import paginate, success
from app.schemas.qa import QAQuestionIn, QAQuestionOut

router = APIRouter(prefix="/qa", tags=["qa"])


def generate_answer(question_text: str) -> str:
    text = question_text.strip().lower()
    if not text:
        return "请先输入具体问题，我会根据你的提问给出学习建议。"

    if "考试" in text or "评测" in text or "测评" in text:
        return (
            "考试相关问题通常围绕课程核心知识点展开。"
            " 建议先复习课程大纲与章节重点，并关注考试时间、提交方式和评分标准。"
        )

    if "章节" in text or "目录" in text or "课程" in text:
        return (
            "从章节目录入手，逐章理解知识点。"
            " 如果某一节内容不明白，可以定位该章节的示例和练习题进行复习。"
        )

    if "作业" in text or "练习" in text or "题" in text:
        return (
            "练习题建议先独立完成，再对照答案解析。"
            " 重点在于理解答案背后的知识点，而不是简单记忆结果。"
        )

    if "为什么" in text or "如何" in text or "是什么" in text:
        return (
            f"这个问题{question_text}通常需要结合课程内容和实际案例来理解。"
            " 建议先回顾相关章节，再用类比和示例帮助记忆。"
        )

    return (
        f"这是智能答疑对问题“{question_text}”的回答：建议先定位问题对应的课程章节，"
        "逐步阅读教材与示例，并结合练习题加深理解。如需更详细帮助，请补充具体场景。"
    )


@router.post("/ask")
def ask_question(payload: QAQuestionIn, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    answer = generate_answer(payload.question)
    question = QAQuestion(
        user_id=current_user.id,
        question=payload.question,
        answer=answer,
        status=QAStatus.answered,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return success(QAQuestionOut.model_validate(question).model_dump(), message="问题已提交并已生成回答")


@router.get("")
def list_questions(
    page: int = 1,
    page_size: int = 20,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(QAQuestion).where(QAQuestion.user_id == current_user.id)
    total = db.execute(
        select(func.count()).select_from(QAQuestion).where(QAQuestion.user_id == current_user.id)
    ).scalar_one()
    items = db.execute(query.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return success(
        paginate(
            [QAQuestionOut.model_validate(item).model_dump() for item in items],
            total,
            page,
            page_size,
        )
    )


@router.get('/ask/stream')
async def stream_answer(
    question_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    question = db.execute(
        select(QAQuestion)
        .where(QAQuestion.id == question_id)
        .where(QAQuestion.user_id == current_user.id)
    ).scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail='问题不存在')

    async def event_generator():
        answer_text = question.answer or f'正在生成对 “{question.question}” 的回答，请稍候。'
        chunks = []
        if question.answer:
            # 已有回答时直接分段返回
            step = max(1, len(answer_text) // 5)
            chunks = [answer_text[i : i + step] for i in range(0, len(answer_text), step)]
        else:
            # 模拟智能答疑生成内容
            prefix = '这是 AI 智能答疑的简要回答：'
            body = f'该问题涉及“{question.question}”，建议重点关注核心概念与示例。'
            answer_text = f'{prefix}{body}'
            step = max(1, len(answer_text) // 6)
            chunks = [answer_text[i : i + step] for i in range(0, len(answer_text), step)]

        for idx, chunk in enumerate(chunks, start=1):
            yield f'data: {chunk}\n\n'
            await asyncio.sleep(0.15)

        # 完成后写入数据库并更新状态
        question.answer = answer_text
        question.status = QAStatus.answered
        db.add(question)
        db.commit()
        yield 'event: done\ndata: done\n\n'

    return StreamingResponse(event_generator(), media_type='text/event-stream')
