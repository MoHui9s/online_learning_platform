"""认证路由：注册 / 登录 / 刷新 / 登出 / 当前用户。

对齐关键决策 1：JWT 存 HttpOnly Cookie + CSRF 双提交。
例外免认证：/auth/register、/auth/login（其余接口需登录）。
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_csrf_token,
    hash_password,
    set_access_cookie,
    set_auth_cookies,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, UserOut
from app.schemas.common import success

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_session(response: Response, user: User) -> None:
    """签发一套 access/refresh/csrf cookie。"""
    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    csrf = generate_csrf_token()
    set_auth_cookies(response, access, refresh, csrf)


@router.post("/register")
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    exists = db.execute(
        select(User).where(
            or_(User.username == payload.username, User.email == payload.email)
        )
    ).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=400, detail="用户名或邮箱已被注册")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hash_password(payload.password),
        nickname=payload.nickname,
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    _issue_session(response, user)
    return success(UserOut.model_validate(user).model_dump(), message="注册成功")


@router.post("/login")
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.execute(
        select(User).where(
            or_(User.username == payload.account, User.email == payload.account)
        )
    ).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已停用")

    _issue_session(response, user)
    return success(UserOut.model_validate(user).model_dump(), message="登录成功")


@router.post("/refresh")
def refresh(request: Request, response: Response):
    """用 refresh cookie 换新的 access cookie。"""
    token = request.cookies.get(settings.REFRESH_COOKIE_NAME)
    payload = decode_token(token, expected_type="refresh") if token else None
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新凭证无效或已过期"
        )
    set_access_cookie(response, create_access_token(payload["sub"]))
    return success(message="已刷新")


@router.post("/logout")
def logout(response: Response, _: User = Depends(get_current_user)):
    clear_auth_cookies(response)
    return success(message="已登出")


@router.get("/me")
def me(current: User = Depends(get_current_user)):
    return success(UserOut.model_validate(current).model_dump())
