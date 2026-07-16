"""v1 路由聚合。新增模块路由在此挂载。"""
from fastapi import APIRouter

from app.api.v1 import auth, categories, courses, courseware,assistant,exams,knowledge_points,qa,questions,stats,wrong_questions,

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(knowledge_points.router)
api_router.include_router(questions.router)
api_router.include_router(exams.router)
api_router.include_router(exams.my_router)
api_router.include_router(wrong_questions.router)
api_router.include_router(qa.router)
api_router.include_router(assistant.router)
api_router.include_router(stats.router)
api_router.include_router(auth.user_router)
api_router.include_router(categories.router)
api_router.include_router(courses.router)
api_router.include_router(courseware.router)
