"""用户资料路由：获取 / 更新当前用户资料。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import UpdateProfileRequest, UserOut
from app.schemas.common import success

router = APIRouter(prefix="/users", tags=["users"])


@router.put("/me")
def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新当前用户资料（全字段可选，只更新传入的字段）。"""
    updated = False

    if payload.nickname is not None:
        current_user.nickname = payload.nickname or None
        updated = True
    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url or None
        updated = True

    # 修改密码需同时传 current_password + new_password
    if payload.new_password is not None or payload.current_password is not None:
        if not payload.current_password or not payload.new_password:
            raise HTTPException(
                status_code=400, detail="修改密码需同时提供当前密码和新密码"
            )
        if not verify_password(payload.current_password, current_user.password_hash):
            raise HTTPException(status_code=400, detail="当前密码错误")
        current_user.password_hash = hash_password(payload.new_password)
        updated = True

    if not updated:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return success(UserOut.model_validate(current_user).model_dump(), message="资料已更新")
