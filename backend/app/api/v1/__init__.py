"""v1 路由聚合。新增模块路由在此挂载。"""
from fastapi import APIRouter

from app.api.v1 import (
    auth,
    exams,
    knowledge_points,
    questions,
    wrong_questions,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(knowledge_points.router)
api_router.include_router(questions.router)
api_router.include_router(exams.router)
api_router.include_router(exams.my_router)
api_router.include_router(wrong_questions.router)
