# backend/seeder.py
import csv
import os
from passlib.context import CryptContext
from .database import SessionLocal, engine
from . import models

# 密码加密配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def seed_users(db):
    """初始化管理员、风控和律师账号"""
    if db.query(models.User).first():
        print("用户数据已存在，跳过初始化。")
        return
    
    users = [
        models.User(username="admin", password=get_password_hash("F_7aE>$=j.qM}YV"), role=models.RoleEnum.ADMIN, full_name="超级管理员"),
        models.User(username="risk", password=get_password_hash("$6)AAnK&+_tEjBs"), role=models.RoleEnum.RISK_CONTROL, full_name="风控专员"),        
    ]
    db.add_all(users)
    db.commit()
    print("初始账号:admin/F_7aE>$=j.qM}YV,risk/$6)AAnK&+_tEjBs")

def seed_dicts(db):
    """从 CSV 文件导入字典数据"""
    if db.query(models.DictionaryTopic).first():
        print("字典数据已存在，跳过导入。")
        return
        
    csv_files = {
        "admin_cause": "dict_admin_causes.csv",
        "civil_cause": "dict_civil_causes.csv",
        "criminal_charge": "dict_criminal_charges.csv",
        "region": "dict_regions.csv"
    }
    
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    
    for category, filename in csv_files.items():
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            print(f"找不到文件: {filepath}，请确保已将其放入 backend/data/ 目录。")
            continue
            
        with open(filepath, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                topic = models.DictionaryTopic(
                    id=int(row['id']),
                    parent_id=int(row['parent_id']),
                    name=row['name'].strip(),
                    level=int(row['level']),
                    category=category
                )
                db.add(topic)
                count += 1
            db.commit()
            print(f"成功导入 {count} 条 [{category}] 字典数据。")

def seed_settings(db):
    """初始化系统配置（律所名称）"""
    if db.query(models.SystemSetting).filter_by(key="firm_name").first():
        return
    setting = models.SystemSetting(key="firm_name", value="成立律师事务所", description="系统生成的案号所使用的律所名称")
    db.add(setting)
    db.commit()
    print("初始系统设置（律所名称）创建成功！")

def main():
    # 确保表已经创建
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        print("开始初始化数据库...")
        seed_users(db)
        seed_settings(db)
        seed_dicts(db)
        print("数据库全面初始化完成！")
    finally:
        db.close()

if __name__ == "__main__":
    main()
