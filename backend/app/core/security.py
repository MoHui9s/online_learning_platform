"""安全工具：密码哈希、JWT 签发/校验、CSRF token、Cookie 下发。

对齐关键决策 1：JWT 存 HttpOnly Cookie + CSRF 双提交。
"""
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Response
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ---------- 密码 ----------
def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ---------- JWT ----------
def _create_token(subject: str | int, expires_minutes: int, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(subject: str | int) -> str:
    return _create_token(subject, settings.JWT_ACCESS_EXPIRE_MINUTES, "access")


def create_refresh_token(subject: str | int) -> str:
    return _create_token(subject, settings.JWT_REFRESH_EXPIRE_MINUTES, "refresh")


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any] | None:
    """解析 JWT；非法/过期/类型不符返回 None。"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        return None
    if expected_type and payload.get("type") != expected_type:
        return None
    return payload


# ---------- CSRF ----------
def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


# ---------- Cookie ----------
def _samesite() -> str:
    return settings.cookie_samesite_value


def set_auth_cookies(response: Response, access: str, refresh: str, csrf: str) -> None:
    """下发三枚 cookie：access/refresh 为 HttpOnly，csrf 前端可读。"""
    domain = settings.COOKIE_DOMAIN or None
    common = dict(
        secure=settings.COOKIE_SECURE,
        samesite=_samesite(),
        domain=domain,
        path="/",
    )
    response.set_cookie(
        settings.ACCESS_COOKIE_NAME,
        access,
        max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
        httponly=True,
        **common,
    )
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        refresh,
        max_age=settings.JWT_REFRESH_EXPIRE_MINUTES * 60,
        httponly=True,
        **common,
    )
    # CSRF token：非 HttpOnly，供前端读取后回填到 X-CSRF-Token
    response.set_cookie(
        settings.CSRF_COOKIE_NAME,
        csrf,
        max_age=settings.JWT_REFRESH_EXPIRE_MINUTES * 60,
        httponly=False,
        **common,
    )


def set_access_cookie(response: Response, access: str) -> None:
    """仅刷新 access（/auth/refresh 用）。"""
    response.set_cookie(
        settings.ACCESS_COOKIE_NAME,
        access,
        max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=_samesite(),
        domain=settings.COOKIE_DOMAIN or None,
        path="/",
    )


def clear_auth_cookies(response: Response) -> None:
    domain = settings.COOKIE_DOMAIN or None
    for name in (
        settings.ACCESS_COOKIE_NAME,
        settings.REFRESH_COOKIE_NAME,
        settings.CSRF_COOKIE_NAME,
    ):
        response.delete_cookie(name, domain=domain, path="/")
