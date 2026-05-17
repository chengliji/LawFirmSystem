# backend/routers/user_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, database, schemas, auth

router = APIRouter(prefix="/api/users", tags=["用户与律师管理"])

def check_admin_or_risk(user: models.User):
    """权限校验辅助函数"""
    if user.role not in [models.RoleEnum.ADMIN, models.RoleEnum.RISK_CONTROL]:
        raise HTTPException(status_code=403, detail="权限不足，仅管理员和风控可用")

@router.get("/lawyers")
def get_lawyers(db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """获取所有律师列表"""
    check_admin_or_risk(current_user)
    # 只查出角色为律师的用户
    lawyers = db.query(models.User).filter(models.User.role == models.RoleEnum.LAWYER).order_by(models.User.id.desc()).all()
    
    return [{
        "id": l.id,
        "username": l.username,
        "full_name": l.full_name,
        "gender": l.gender.value if l.gender else "",
        "license_no": l.license_no,
        "license_type": l.license_type.value if l.license_type else "",
        "phone": l.phone,
        "status": l.status.value
    } for l in lawyers]

@router.post("/lawyers")
def add_lawyer(req: schemas.LawyerCreate, db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """新增律师"""
    check_admin_or_risk(current_user)
    
    # 检查用户名是否冲突
    if db.query(models.User).filter(models.User.username == req.username).first():
        raise HTTPException(status_code=400, detail="该登录账号已存在")
        
    new_lawyer = models.User(
        username=req.username,
        password=auth.get_password_hash(req.password),
        role=models.RoleEnum.LAWYER,
        full_name=req.full_name,
        gender=req.gender,
        license_no=req.license_no,
        license_type=req.license_type,
        phone=req.phone,
        status=models.StatusEnum.ACTIVE
    )
    db.add(new_lawyer)
    db.commit()
    return {"message": "新增律师成功"}

@router.put("/lawyers/{user_id}")
def update_lawyer(user_id: int, req: schemas.LawyerUpdate, db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """修改律师信息及状态"""
    check_admin_or_risk(current_user)
    lawyer = db.query(models.User).filter(models.User.id == user_id, models.User.role == models.RoleEnum.LAWYER).first()
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")     
    lawyer.full_name = req.full_name
    lawyer.gender = req.gender
    lawyer.license_no = req.license_no
    lawyer.license_type = req.license_type
    lawyer.phone = req.phone
    lawyer.status = req.status 
    db.commit()
    return {"message": "信息修改成功"}

@router.put("/lawyers/{user_id}/password")
def reset_password(user_id: int, req: schemas.PasswordReset, db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """修改律师密码"""
    check_admin_or_risk(current_user)
    lawyer = db.query(models.User).filter(models.User.id == user_id, models.User.role == models.RoleEnum.LAWYER).first()
    if not lawyer:
        raise HTTPException(status_code=404, detail="律师不存在")
        
    lawyer.password = auth.get_password_hash(req.new_password)
    db.commit()
    return {"message": "密码修改成功"}

@router.delete("/lawyers/{user_id}")
def delete_lawyer(user_id: int, db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """彻底删除律师账号（仅管理员）"""
    if current_user.role != models.RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="权限不足：仅管理员有权限删除律师账号")
        
    # 强制安全检查：如果律师作为“创建者”或“承办律师”参与过案件，严禁删除以防数据断层
    has_created = db.query(models.Case).filter(models.Case.creator_id == user_id).first()
    has_involved = db.query(models.CaseInternalLawyer).filter(models.CaseInternalLawyer.lawyer_id == user_id).first()
    
    if has_created or has_involved:
        raise HTTPException(status_code=400, detail="该律师名下已有历史案件关联记录。为保证业务数据完整性，系统禁止删除，请将其状态设置为【离职】！")
        
    db.query(models.User).filter(models.User.id == user_id).delete()
    db.commit()
    return {"message": "律师账号已彻底删除"}

@router.put("/me/password")
def update_self_password(req: schemas.PasswordReset, db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """律师/用户自行修改个人密码"""
    user = db.query(models.User).filter(models.User.id == current_user.id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.password = auth.get_password_hash(req.new_password)
    db.commit()
    return {"message": "密码修改成功，请重新登录"}