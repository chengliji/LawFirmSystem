# backend/routers/dict_router.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, database, auth

router = APIRouter(prefix="/api/dicts", tags=["字典与通用下拉数据"])

@router.get("/topics")
def get_topics(category: str, keyword: str = "", db: Session = Depends(database.get_db)):
    """异步搜索：根据分类和关键字查询字典库 [cite: 17, 18, 19, 20]"""
    query = db.query(models.DictionaryTopic).filter(models.DictionaryTopic.category == category)
    
    if keyword:
        # 模糊匹配名称
        query = query.filter(models.DictionaryTopic.name.ilike(f"%{keyword}%"))
        
    # 限制返回数量，防止前端卡顿
    results = query.limit(50).all()
    return [{"id": r.id, "name": r.name} for r in results]

@router.get("/lawyers")
def get_active_lawyers(db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """获取所有在职律师列表，供收案分配使用 [cite: 1, 2, 3, 4]"""
    lawyers = db.query(models.User).filter(
        models.User.role == models.RoleEnum.LAWYER,
        models.User.status == models.StatusEnum.ACTIVE
    ).all()
    return [{"id": l.id, "name": f"{l.full_name} ({l.license_type.value if l.license_type else '未知'})"} for l in lawyers]