"""CSRF 双提交中间件（对齐关键决策 1）。

对写方法(POST/PUT/DELETE/PATCH)校验 header(X-CSRF-Token) == cookie(csrf_token)。
豁免：安全方法(GET/HEAD/OPTIONS) 与 登录/注册(尚无会话)。
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
# 无会话时豁免的路径（登录/注册）
EXEMPT_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register"}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in SAFE_METHODS and request.url.path not in EXEMPT_PATHS:
            header = request.headers.get(settings.CSRF_HEADER_NAME)
            cookie = request.cookies.get(settings.CSRF_COOKIE_NAME)
            if not header or not cookie or header != cookie:
                return JSONResponse(
                    status_code=403,
                    content={
                        "code": 403,
                        "data": None,
                        "message": "CSRF 校验失败",
                    },
                )
        return await call_next(request)
