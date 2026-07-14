"""FastAPI 入口：挂载路由、中间件(CORS/CSRF)、统一异常处理。"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1 import api_router
from app.core.config import settings
from app.core.csrf import CSRFMiddleware

app = FastAPI(title=settings.APP_NAME, version="0.1.0")

# --- CORS：允许携带 cookie，源必须精确（不能用 *） ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", settings.CSRF_HEADER_NAME],
)

# --- CSRF 双提交（写操作校验，登录/注册豁免） ---
app.add_middleware(CSRFMiddleware)


# --- 统一异常 -> 统一响应体 ---
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "data": None, "message": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"code": 422, "data": exc.errors(), "message": "请求参数校验失败"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "data": None, "message": "服务器内部错误"},
    )


# --- 健康检查（无需认证） ---
@app.get("/health", tags=["system"])
def health():
    return {"code": 200, "data": {"status": "ok"}, "message": "success"}


app.include_router(api_router)
