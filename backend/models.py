# backend/models.py
from sqlalchemy import Column, Integer, String, BigInteger, Boolean, ForeignKey, Text, Date, DateTime, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from .database import Base

# 枚举定义
class RoleEnum(str, enum.Enum):
    ADMIN = "管理员"
    LAWYER = "律师"
    RISK_CONTROL = "风控"

class GenderEnum(str, enum.Enum):
    MALE = "男"
    FEMALE = "女"
    OTHER = "未知"

class LicenseTypeEnum(str, enum.Enum):
    FULL_TIME = "专职律师"
    PART_TIME = "兼职律师"

class StatusEnum(str, enum.Enum):
    ACTIVE = "在职"
    INACTIVE = "离职"

class EntityTypeEnum(str, enum.Enum):
    PERSON = "自然人"
    ENTERPRISE = "企业"
    GOVERNMENT = "政府"
    NGO = "社会组织及其它"

class CaseTypeEnum(str, enum.Enum):
    CRIMINAL = "刑事案件"
    CIVIL = "民事案件"
    ADMIN = "行政案件"
    ARBITRATION = "仲裁案件"
    CONSULTANT = "顾问案件"
    NON_LITIGATION = "非诉案件"

class CaseSourceEnum(str, enum.Enum):
    PERSONAL = "个人案源"
    PUBLIC = "公共案源"

class CaseStatusEnum(str, enum.Enum):
    CASE_REVIEW = "案件审核"
    CONTRACT_REVIEW = "合同审核"
    CLOSE_REVIEW = "结案审核"
    CLOSED = "已结案"

class ProcessTagEnum(str, enum.Enum):
    NORMAL = "正常"
    VOID = "案件作废"
    TERMINATED = "合同解除"

# 模型定义

class SystemSetting(Base):
    """系统设置表：存储律所名称等动态配置"""
    __tablename__ = 'system_settings'
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False, index=True)
    value = Column(String(255), nullable=False)
    description = Column(String(255))

class DictionaryTopic(Base):
    """字典表：整合案由、罪名、省市级联数据"""
    __tablename__ = 'dictionary_topics'
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, default=0, index=True)
    name = Column(String(255), nullable=False)
    level = Column(Integer, nullable=False)
    category = Column(String(50), nullable=False, index=True)

class User(Base):
    """用户/律师表"""
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(SQLEnum(RoleEnum), nullable=False)
    full_name = Column(String(100), nullable=False)
    gender = Column(SQLEnum(GenderEnum))
    license_no = Column(String(100))
    license_type = Column(SQLEnum(LicenseTypeEnum))
    phone = Column(String(20))
    status = Column(SQLEnum(StatusEnum), default=StatusEnum.ACTIVE)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ExternalEntity(Base):
    """外部主体表"""
    __tablename__ = 'external_entities'
    id = Column(BigInteger, primary_key=True, index=True)
    entity_type = Column(SQLEnum(EntityTypeEnum), nullable=False)
    name = Column(String(255), nullable=False, index=True)
    id_type = Column(String(50)) 
    id_number = Column(String(100), index=True)
    contact_person = Column(String(100))
    phone = Column(String(50))
    is_verified = Column(Boolean, default=False)

class Case(Base):
    """案件主表"""
    __tablename__ = 'cases'
    id = Column(BigInteger, primary_key=True, index=True)
    serial_no = Column(String(50), unique=True, index=True)
    case_no = Column(String(100), unique=True, index=True, nullable=True)
    title = Column(String(255), nullable=False)
    case_type = Column(SQLEnum(CaseTypeEnum), nullable=False)
    source = Column(SQLEnum(CaseSourceEnum), nullable=False)
    status = Column(SQLEnum(CaseStatusEnum), default=CaseStatusEnum.CASE_REVIEW)
    process_tag = Column(SQLEnum(ProcessTagEnum), default=ProcessTagEnum.NORMAL)
    reg_date = Column(Date, default=lambda: datetime.now(timezone.utc).date())
    close_date = Column(Date, nullable=True)
    description = Column(Text)
    creator_id = Column(BigInteger, ForeignKey('users.id'))
    is_conflict_waived = Column(Boolean, default=False)
    
    # 关联
    creator = relationship("User")
    details = relationship("CaseDetail", back_populates="case", uselist=False)
    external_relations = relationship("CaseExternalRelation", back_populates="case")
    internal_lawyers = relationship("CaseInternalLawyer", back_populates="case")
    stages = relationship("CaseStageMap", back_populates="case")
    finance = relationship("CaseFinance", back_populates="case", uselist=False)

class CaseDetail(Base):
    """案件扩展详情表"""
    __tablename__ = 'case_details'
    case_id = Column(BigInteger, ForeignKey('cases.id'), primary_key=True)
    criminal_type = Column(String(50))
    topic_id = Column(Integer, ForeignKey('dictionary_topics.id'), nullable=True)
    region_id = Column(Integer, ForeignKey('dictionary_topics.id'), nullable=True)
    agency_names = Column(Text)
    is_legal_aid = Column(Boolean, default=False)
    is_foreign = Column(Boolean, default=False)
    service_start = Column(Date, nullable=True)
    service_end = Column(Date, nullable=True)
    case = relationship("Case", back_populates="details")

class CaseExternalRelation(Base):
    """外部人员关联表"""
    __tablename__ = 'case_external_relations'
    id = Column(BigInteger, primary_key=True, index=True)
    case_id = Column(BigInteger, ForeignKey('cases.id'))
    entity_id = Column(BigInteger, ForeignKey('external_entities.id'))
    role_name = Column(String(50))
    case = relationship("Case", back_populates="external_relations")
    entity = relationship("ExternalEntity")

class CaseInternalLawyer(Base):
    """内部律师关联与分配表"""
    __tablename__ = 'case_internal_lawyers'
    id = Column(BigInteger, primary_key=True, index=True)
    case_id = Column(BigInteger, ForeignKey('cases.id'))
    lawyer_id = Column(BigInteger, ForeignKey('users.id'))
    role_type = Column(String(50))
    allocation_ratio = Column(Numeric(5, 2), default=100.00)
    case = relationship("Case", back_populates="internal_lawyers")
    lawyer = relationship("User")

class CaseStageMap(Base):
    """委托阶段关联表"""
    __tablename__ = 'case_stage_map'
    id = Column(BigInteger, primary_key=True, index=True)
    case_id = Column(BigInteger, ForeignKey('cases.id'))
    stage_tag = Column(String(50))
    case = relationship("Case", back_populates="stages")

class CaseFinance(Base):
    """财务信息表"""
    __tablename__ = 'case_finances'
    case_id = Column(BigInteger, ForeignKey('cases.id'), primary_key=True)
    billing_method = Column(String(50))
    target_amount = Column(Numeric(15, 2), default=0.00)
    receivable = Column(Numeric(15, 2), default=0.00)
    received = Column(Numeric(15, 2), default=0.00)
    fee_remark = Column(Text)
    case = relationship("Case", back_populates="finance")

class CaseDocument(Base):
    """文档存储表"""
    __tablename__ = 'case_documents'
    id = Column(BigInteger, primary_key=True, index=True)
    case_id = Column(BigInteger, ForeignKey('cases.id'))
    doc_type = Column(String(50))
    file_name = Column(String(255))
    file_path = Column(String(500))
    uploader_id = Column(BigInteger, ForeignKey('users.id'))
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class CaseOperationLog(Base):
    """案件操作日志表"""
    __tablename__ = 'case_operation_logs'
    id = Column(BigInteger, primary_key=True, index=True)
    case_id = Column(BigInteger, ForeignKey('cases.id', ondelete='CASCADE'))
    operator_id = Column(BigInteger, ForeignKey('users.id'))
    operator_name = Column(String(50))
    action = Column(String(255))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))