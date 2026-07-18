"""v1 路由聚合。新增模块路由在此挂载。"""
from fastapi import APIRouter

from app.api.v1 import auth, categories, courses, coursewares, exam, learning, qa, stats, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(courses.router)
api_router.include_router(categories.router)
api_router.include_router(coursewares.router)
api_router.include_router(learning.router)
api_router.include_router(qa.router)
api_router.include_router(exam.router)
api_router.include_router(stats.router)
api_router.include_router(users.router)
