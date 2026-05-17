# backend/routers/auth_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, database, schemas, auth
from datetime import timedelta

router = APIRouter(prefix="/api/auth", tags=["认证中心"])

@router.post("/login", response_model=schemas.Token)
def login(login_data: schemas.LoginRequest, db: Session = Depends(database.get_db)):
    """
    用户登录接口：验证账号密码，返回 JWT Token 和用户信息
    """
    # 查找用户
    user = db.query(models.User).filter(models.User.username == login_data.username).first()
    
    # 校验是否存在且密码正确
    if not user or not auth.verify_password(login_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    
    # 校验用户状态
    if user.status != models.StatusEnum.ACTIVE:
        raise HTTPException(status_code=403, detail="该账户已离职或被禁用，请联系管理员")

    # 生成 Token
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role.value}, # 保存账号和角色到载荷
        expires_delta=access_token_expires
    )
    
    # 返回符合 Token schema 的数据
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role.value
        }
    }