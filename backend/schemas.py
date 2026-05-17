# backend/schemas.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
from decimal import Decimal

# 接收前端传来的 JSON 登录表单
class LoginRequest(BaseModel):
    username: str
    password: str

# 返回给前端的用户基本信息
class UserResponse(BaseModel):
    id: int
    username: str
    full_name: str
    role: str

# 返回的 Token 结构
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse   

# 案件人员子模型
class EntityCreate(BaseModel):
    entity_type: str
    name: str
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    role_name: str

# 律师分配子模型
class LawyerAssign(BaseModel):
    lawyer_id: int
    role_type: str
    allocation_ratio: float = 100.0

# 冲突检索请求模型
class ConflictCheckRequest(BaseModel):
    entities: List[EntityCreate]

# 收案登记主表单模型
class CaseRegisterRequest(BaseModel):
    # 基础信息 (cases 表)
    title: str
    case_type: str
    source: str
    is_conflict_waived: bool = False
    description: Optional[str] = None
    
    # 案件人员
    entities: List[EntityCreate]
    
    # 详情信息 (case_details 表)
    criminal_type: Optional[str] = None
    topic_id: Optional[int] = None
    region_id: Optional[int] = None
    agency_names: Optional[str] = None
    is_legal_aid: bool = False
    is_foreign: bool = False
    service_start: Optional[date] = None
    service_end: Optional[date] = None
    
    # 委托阶段
    stages: List[str]
    
    # 内部律师
    lawyers: List[LawyerAssign]
    
    # 财务信息 (case_finances 表)
    billing_method: str
    target_amount: Decimal = Decimal('0.00')
    receivable: Decimal = Decimal('0.00')
    received: Decimal = Decimal('0.00')
    fee_remark: Optional[str] = None

# 新增律师
class LawyerCreate(BaseModel):
    username: str
    password: str
    full_name: str
    gender: str
    license_no: str
    license_type: str
    phone: str

# 编辑律师
class LawyerUpdate(BaseModel):
    full_name: str
    gender: str
    license_no: str
    license_type: str
    phone: str
    status: str

# 密码重设
class PasswordReset(BaseModel):
    new_password: str