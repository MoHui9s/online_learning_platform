"""C5: AI 学习助手路由。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.common import success
from app.schemas.qa import SimilarQuestionRequest
from app.services.agent_service import generate_similar_questions, generate_suggestions

router = APIRouter(tags=["assistant"])


@router.get("/assistant/suggestions")
def get_suggestions(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """生成个性化学习建议，基于错题数据分析薄弱知识点。"""
    result = generate_suggestions(db, current.id)
    return success(result)


@router.post("/assistant/similar-questions")
def get_similar_questions(
    payload: SimilarQuestionRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """举一反三：基于错题生成/查找变式题。"""
    result = generate_similar_questions(db, payload.wrong_question_id, current.id)
    if result is None:
        raise HTTPException(status_code=404, detail="错题记录不存在")
    return success(result)
