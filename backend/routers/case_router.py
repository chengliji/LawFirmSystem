# backend/routers/case_router.py
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from decimal import Decimal
from .. import models, database, schemas, auth
from sqlalchemy import func, extract, or_
from typing import Optional, List
import csv
import io
from fastapi.responses import StreamingResponse
from urllib.parse import quote
import re
from datetime import datetime
import os
import shutil
import pandas as pd
from io import BytesIO

router = APIRouter(prefix="/api/cases", tags=["案件管理"])

@router.post("/conflict-check")
def check_conflict(req: schemas.ConflictCheckRequest, db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """
    冲突检索：依据当事人的名称或证件号，查询是否在 external_entities 中存在，
    若存在，则关联查询出其参与的历史案件。
    """
    conflicts = []
    
    for entity in req.entities:
        if not entity.name and not entity.id_number:
            continue
            
        # 构建查询条件：名字相同 或 证件号相同
        conditions = []
        if entity.name:
            conditions.append(models.ExternalEntity.name == entity.name)
        if entity.id_number:
            conditions.append(models.ExternalEntity.id_number == entity.id_number)
            
        # 查询是否存在该人员
        existing_entities = db.query(models.ExternalEntity).filter(or_(*conditions)).all()
        
        for ee in existing_entities:
            # 如果存在，查询关联的历史案件
            relations = db.query(models.CaseExternalRelation).filter(
                models.CaseExternalRelation.entity_id == ee.id
            ).all()
            
            for rel in relations:
                c = rel.case
                creator_name = c.creator.full_name if c.creator else "未知"
                conflicts.append({
                    "serial_no": c.serial_no,
                    "title": c.title,
                    "case_type": c.case_type.value,
                    "lawyer": creator_name,
                    "reg_date": c.reg_date,
                    "status": c.status.value,
                    "conflict_name": ee.name
                })
                
    return {
        "has_conflict": len(conflicts) > 0,
        "conflicts": conflicts
    }

@router.post("/register")
def register_case(req: schemas.CaseRegisterRequest, db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """
    收案登记核心接口：跨 6 张表的数据事务插入
    """
    try:
        # 生成流水号 N + 5位数字 (N10001 开始)
        last_case = db.query(models.Case).filter(models.Case.serial_no.like('N%')).order_by(models.Case.id.desc()).first()
        next_num = 10001
        if last_case and last_case.serial_no:
            try:
                next_num = int(last_case.serial_no[1:]) + 1
            except ValueError:
                pass
        new_serial = f"N{next_num}"

        # 插入案件主表 (cases)
        new_case = models.Case(
            serial_no=new_serial,
            title=req.title,
            case_type=req.case_type,
            source=req.source,
            status=models.CaseStatusEnum.CASE_REVIEW,
            description=req.description,
            creator_id=current_user.id,
            is_conflict_waived=req.is_conflict_waived
        )
        db.add(new_case)
        db.flush()

        # 处理案件人员 (external_entities & case_external_relations)
        for e in req.entities:
            # 查找是否已存在该主体 (通过证件号优先，其次名称)
            ee_query = db.query(models.ExternalEntity)
            if e.id_number:
                ee = ee_query.filter(models.ExternalEntity.id_number == e.id_number).first()
            else:
                ee = ee_query.filter(models.ExternalEntity.name == e.name).first()
                
            # 如果不存在则新建外部主体
            if not ee:
                ee = models.ExternalEntity(
                    entity_type=e.entity_type, name=e.name, id_type=e.id_type,
                    id_number=e.id_number, contact_person=e.contact_person, phone=e.phone
                )
                db.add(ee)
                db.flush()
                
            # 建立关联
            rel = models.CaseExternalRelation(case_id=new_case.id, entity_id=ee.id, role_name=e.role_name)
            db.add(rel)

        # 插入案件详情 (case_details)
        # 业务逻辑拦截：只要选择了法律援助，应收和已收强制置零
        if req.is_legal_aid:
            req.receivable = Decimal('0.00')
            req.received = Decimal('0.00')

        detail = models.CaseDetail(
            case_id=new_case.id, criminal_type=req.criminal_type, topic_id=req.topic_id,
            region_id=req.region_id, agency_names=req.agency_names, is_legal_aid=req.is_legal_aid,
            is_foreign=req.is_foreign, service_start=req.service_start, service_end=req.service_end
        )
        db.add(detail)

        # 插入委托阶段 (case_stage_map)
        for stage in req.stages:
            db.add(models.CaseStageMap(case_id=new_case.id, stage_tag=stage))

        # 插入委托律师 (case_internal_lawyers)
        for lw in req.lawyers:
            db.add(models.CaseInternalLawyer(case_id=new_case.id, lawyer_id=lw.lawyer_id, role_type=lw.role_type, allocation_ratio=lw.allocation_ratio))

        # 插入财务信息 (case_finances)
        finance = models.CaseFinance(
            case_id=new_case.id, billing_method=req.billing_method,
            target_amount=req.target_amount, receivable=req.receivable,
            received=req.received, fee_remark=req.fee_remark
        )
        db.add(finance)

        # 所有操作无误，正式提交事务
        db.commit()
        return {"message": "收案登记成功", "serial_no": new_serial, "case_id": new_case.id}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"登记失败，数据异常: {str(e)}")




@router.get("/stats")
def get_case_stats(db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """获取案件业务状态统计（已修复权限隔离）"""
    query = db.query(models.Case.status, func.count(models.Case.id)).group_by(models.Case.status)
    
    # 权限隔离：律师可以看到自己创建或参与（内部律师表）的案件
    if current_user.role == models.RoleEnum.LAWYER:
        involved_cases = db.query(models.CaseInternalLawyer.case_id).filter(models.CaseInternalLawyer.lawyer_id == current_user.id)
        query = query.filter(or_(
            models.Case.creator_id == current_user.id,
            models.Case.id.in_(involved_cases)
        ))
        
    results = query.all()
    stats = {"案件审核": 0, "合同审核": 0, "结案审核": 0, "已结案": 0}
    for status, count in results:
        if status.value in stats:
            stats[status.value] = count
    return stats

@router.get("/list")
def get_case_list(
    page: int = 1, size: int = 10, keyword: Optional[str] = None, 
    case_type: Optional[str] = None, status: Optional[str] = None,
    db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)
):
    """获取案件列表（已修复权限隔离）"""
    query = db.query(models.Case)
    
    # 权限隔离
    if current_user.role == models.RoleEnum.LAWYER:
        involved_cases = db.query(models.CaseInternalLawyer.case_id).filter(models.CaseInternalLawyer.lawyer_id == current_user.id)
        query = query.filter(or_(
            models.Case.creator_id == current_user.id,
            models.Case.id.in_(involved_cases)
        ))
        
    # 搜索条件过滤
    if keyword:
        query = query.filter(or_(
            models.Case.title.ilike(f"%{keyword}%"),
            models.Case.serial_no.ilike(f"%{keyword}%"),
            models.Case.case_no.ilike(f"%{keyword}%")
        ))
    if case_type:
        query = query.filter(models.Case.case_type == case_type)
    if status:
        query = query.filter(models.Case.status == status)
        
    total = query.count()
    cases = query.order_by(models.Case.id.desc()).offset((page - 1) * size).limit(size).all()
    
    # 返回值格式化
    result_list = []
    for c in cases:
        main_lawyer_name = "未指定"
        for lw in c.internal_lawyers:
            if lw.role_type == "主办律师" and lw.lawyer:
                main_lawyer_name = lw.lawyer.full_name
                break
        result_list.append({
            "id": c.id, "serial_no": c.serial_no, "case_no": c.case_no or "等待生成",
            "title": c.title, "case_type": c.case_type.value, "main_lawyer": main_lawyer_name,
            "status": c.status.value, "reg_date": c.reg_date.strftime("%Y-%m-%d") if c.reg_date else "",
            "process_tag": c.process_tag.value if c.process_tag else "正常"
        })
        
    return {"total": total, "page": page, "size": size, "items": result_list}



@router.get("/detail/{case_id}")
def get_case_detail(case_id: int, db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    c = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="案件不存在")
        
    # 获取所有参与该案的律师 ID（包含主办和协办）
    involved_lawyer_ids = [lw.lawyer_id for lw in c.internal_lawyers]

    logs = db.query(models.CaseOperationLog).filter(models.CaseOperationLog.case_id == case_id).order_by(models.CaseOperationLog.created_at.desc()).all()
    
    # 权限隔离：律师角色下，既不是创建者也不是参与律师，则无权查看
    if current_user.role == models.RoleEnum.LAWYER:
        if c.creator_id != current_user.id and current_user.id not in involved_lawyer_ids:
            raise HTTPException(status_code=403, detail="您无权查看此案件")

    # 查询案由/罪名名称
    topic_name = ""
    if c.details and c.details.topic_id:
        topic_name = db.query(models.DictionaryTopic.name).filter(models.DictionaryTopic.id == c.details.topic_id).scalar()
        
    # 查询省市名称
    region_name = ""
    if c.details and c.details.region_id:
        region_name = db.query(models.DictionaryTopic.name).filter(models.DictionaryTopic.id == c.details.region_id).scalar()

    # 组装人员信息
    entities = []
    for rel in c.external_relations:
        entities.append({
            "id": rel.entity.id,
            "role_name": rel.role_name,
            "entity_type": rel.entity.entity_type.value,
            "name": rel.entity.name,
            "id_type": rel.entity.id_type,
            "id_number": rel.entity.id_number,
            "phone": rel.entity.phone
        })

    # 组装律师信息
    lawyers = []
    for lw in c.internal_lawyers:
        lawyers.append({
            "lawyer_id": lw.lawyer_id,
            "role_type": lw.role_type,
            "name": lw.lawyer.full_name if lw.lawyer else "未知",
            "allocation_ratio": float(lw.allocation_ratio) if getattr(lw, 'allocation_ratio', None) is not None else 0
        })

    return {
        "id": c.id,
        "serial_no": c.serial_no,
        "case_no": c.case_no,
        "title": c.title,
        "case_type": c.case_type.value,
        "source": c.source.value,
        "status": c.status.value,
        "process_tag": c.process_tag.value if c.process_tag else "正常",
        "reg_date": c.reg_date,
        "description": c.description,
        "details": {
            "criminal_type": c.details.criminal_type if c.details else None,
            "topic_name": topic_name,
            "region_name": region_name,
            "topic_id": c.details.topic_id if c.details else None,
            "region_id": c.details.region_id if c.details else None,
            "agency_names": c.details.agency_names if c.details else None,
            "is_legal_aid": c.details.is_legal_aid if c.details else False,
            "is_foreign": c.details.is_foreign if c.details else False,
            "service_start": c.details.service_start if c.details else None,
            "service_end": c.details.service_end if c.details else None,
        },
        "entities": entities,
        "lawyers": lawyers,
        "stages": [s.stage_tag for s in c.stages],
        "finance": {
            "billing_method": c.finance.billing_method if c.finance else "",
            "target_amount": float(c.finance.target_amount) if c.finance else 0,
            "receivable": float(c.finance.receivable) if c.finance else 0,
            "received": float(c.finance.received) if c.finance else 0,
            "fee_remark": c.finance.fee_remark if c.finance else "",
        "logs": [{"operator": log.operator_name, "action": log.action, "time": log.created_at.strftime("%Y-%m-%d %H:%M:%S")} for log in logs]
        }
    }

@router.put("/detail/{case_id}")
def update_case_detail(case_id: int, req: dict, db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """更新案件详情，并精细记录风控的具体修改内容"""
    if current_user.role == models.RoleEnum.LAWYER:
        raise HTTPException(status_code=403, detail="律师无权修改案件信息")
        
    c = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 用于收集所有变动的文本
    changes = []

    if "title" in req and c.title != req["title"]:
        changes.append(f"案件名称由「{c.title}」改为「{req['title']}」")
        c.title = req["title"]
        
    if "description" in req and (c.description or "") != (req["description"] or ""):
        changes.append("修改了案件说明")
        c.description = req["description"]
    
    if c.finance and "finance" in req:
        fin_data = req["finance"]
        if "target_amount" in fin_data and float(c.finance.target_amount) != float(fin_data["target_amount"]):
            changes.append(f"标的额由 {c.finance.target_amount} 修改为 {fin_data['target_amount']}")
            c.finance.target_amount = fin_data["target_amount"]
            
        if "receivable" in fin_data and float(c.finance.receivable) != float(fin_data["receivable"]):
            changes.append(f"应收金额由 {c.finance.receivable} 修改为 {fin_data['receivable']}")
            c.finance.receivable = fin_data["receivable"]
            
        if "received" in fin_data and float(c.finance.received) != float(fin_data["received"]):
            changes.append(f"已收金额由 {c.finance.received} 修改为 {fin_data['received']}")
            c.finance.received = fin_data["received"]
            
        if "fee_remark" in fin_data and (c.finance.fee_remark or "") != (fin_data["fee_remark"] or ""):
            changes.append("修改了收费说明")
            c.finance.fee_remark = fin_data["fee_remark"]

    # 如果有任何实质性修改，将其写入日志表
    if changes:
        action_text = "；".join(changes)
        db.add(models.CaseOperationLog(
            case_id=c.id,
            operator_id=current_user.id,
            operator_name=current_user.full_name,
            action=action_text
        ))

    db.commit()
    return {"message": "案件信息更新成功"}



@router.get("/dashboard/metrics")
def get_dashboard_metrics(db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """获取控制台首页真实业务指标与图表数据（已修复律师权限隔离）"""
    from datetime import datetime
    now = datetime.now()
    
    # 基础查询构造器
    query_cases = db.query(models.Case)
    query_clients = db.query(models.ExternalEntity)
    
    # 权限隔离：律师仅统计自己参与的案件
    if current_user.role == models.RoleEnum.LAWYER:
        involved_cases = db.query(models.CaseInternalLawyer.case_id).filter(models.CaseInternalLawyer.lawyer_id == current_user.id)
        query_cases = query_cases.filter(or_(
            models.Case.creator_id == current_user.id,
            models.Case.id.in_(involved_cases)
        ))
        # 律师的客户：仅统计与其参与案件关联的客户
        involved_clients = db.query(models.CaseExternalRelation.entity_id).filter(
            models.CaseExternalRelation.case_id.in_(
                db.query(models.Case.id).filter(or_(
                    models.Case.creator_id == current_user.id,
                    models.Case.id.in_(involved_cases)
                ))
            )
        )
        query_clients = query_clients.filter(models.ExternalEntity.id.in_(involved_clients))

    # 本月案件
    month_cases = query_cases.filter(
        extract('year', models.Case.reg_date) == now.year,
        extract('month', models.Case.reg_date) == now.month
    ).count()

    # 累计案件
    total_cases = query_cases.count()

    # 服务客户
    total_clients = query_clients.count()

    # 案件类型分布图表数据
    type_distribution = db.query(models.Case.case_type, func.count(models.Case.id)).filter(
        models.Case.id.in_(query_cases.with_entities(models.Case.id))
    ).group_by(models.Case.case_type).all()
    
    pie_data = [{"name": t.value, "value": c} for t, c in type_distribution]

    return {
        "month_cases": month_cases,
        "total_cases": total_cases,
        "total_clients": total_clients,
        "pie_data": pie_data
    }


@router.post("/approve/{case_id}")
def approve_case_workflow(case_id: int, db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """风控审核状态流转引擎 & 案号自动生成（修复乱序审核重号问题）"""
    if current_user.role == models.RoleEnum.LAWYER:
        raise HTTPException(status_code=403, detail="仅风控或管理员可进行审核")
        
    c = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="案件不存在")

    # 状态 ：案件审核 -> 合同审核（在此处生成案号）
    if c.status == models.CaseStatusEnum.CASE_REVIEW:
        current_year = str(datetime.now().year)
        cases_this_year = db.query(models.Case.case_no).filter(
            models.Case.case_no.like(f"%{current_year}%")
        ).all()
        
        max_num = 101
        
        # 遍历当年所有案号，通过正则提取数字并找出最大值
        for case_record in cases_this_year:
            existing_no = case_record[0]
            if existing_no:
                match = re.search(r'第(\d+)号', existing_no)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
                        
        next_num = max_num + 1
                
        # 获取律所名称
        firm_setting = db.query(models.SystemSetting).filter_by(key="firm_name").first()
        firm_name = firm_setting.value[:2] if firm_setting else "成立"
        
        # 格式：{年份}+律所名+{案件类型}+第+{数字 101 开始}+号
        c.case_no = f"（{current_year}）{firm_name}{c.case_type.value[:2]}第{next_num}号"
        c.status = models.CaseStatusEnum.CONTRACT_REVIEW
        message = f"审核通过，已生成案号：{c.case_no}"

    # 状态 ：合同审核 -> 结案审核
    elif c.status == models.CaseStatusEnum.CONTRACT_REVIEW:
        c.status = models.CaseStatusEnum.CLOSE_REVIEW
        message = "合同审核通过，进入结案审核阶段"
        
    # 状态 ：结案审核 -> 已结案
    elif c.status == models.CaseStatusEnum.CLOSE_REVIEW:
        c.status = models.CaseStatusEnum.CLOSED
        c.close_date = datetime.now().date()
        message = "结案审核通过，案件已结案"
    else:
        raise HTTPException(status_code=400, detail="该案件已完结或处于异常状态")

    db.commit()
    return {"message": message, "new_status": c.status.value}

# 确保 uploads 文件夹存在
os.makedirs("uploads", exist_ok=True)

@router.post("/upload")
def upload_case_document(
    case_id: int = Form(...), 
    doc_type: str = Form(...), 
    file: UploadFile = File(...), 
    db: Session = Depends(database.get_db), 
    current_user=Depends(auth.get_current_user)
):
    """处理真实的物理文件上传"""
    c = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="案件不存在")
        
    # 生成安全的文件名：时间戳_原文件名
    safe_filename = f"{int(datetime.now().timestamp())}_{file.filename}"
    file_path = os.path.join("uploads", safe_filename)
    
    # 将文件写入磁盘
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 写入数据库记录
    new_doc = models.CaseDocument(
        case_id=case_id,
        doc_type=doc_type,
        file_name=file.filename,
        file_path=file_path,
        uploader_id=current_user.id
    )
    db.add(new_doc)
    db.commit()
    
    return {"message": f"{doc_type} 上传成功", "file_path": file_path}


@router.put("/process-tag/{case_id}")
def update_process_tag(case_id: int, req: dict, db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """修改案件的 process_tag (作废或解除)"""
    if current_user.role == models.RoleEnum.LAWYER:
        raise HTTPException(status_code=403, detail="仅风控或管理员可进行此操作")
        
    c = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="案件不存在")
        
    tag = req.get("tag")
    if tag == "案件作废":
        c.process_tag = models.ProcessTagEnum.VOID
    elif tag == "合同解除":
        c.process_tag = models.ProcessTagEnum.TERMINATED
    elif tag == "正常":
        c.process_tag = models.ProcessTagEnum.NORMAL
    else:
        raise HTTPException(status_code=400, detail="无效的状态标签")
        
    db.commit()
    return {"message": f"案件已标记为：{tag}"}



def _generate_csv_stream(cases: List[models.Case], db: Session) -> io.StringIO:
    """内部辅助方法：生成标准化的横向宽表 CSV 数据流（模板标准）"""
    stream = io.StringIO()
    writer = csv.writer(stream)
    stream.write('\ufeff')
    
    # 严格定义模板表头（涵盖收案登记的所有字段）
    headers = [
        "流水号", "案号", "案件名称", "案件类型", "案件来源", "当前状态", "异常标记", "登记日期", 
        "案件说明", "案由/罪名", "办案机关省市", "办案机关名称", "刑事类型", "是否法律援助", 
        "是否涉外", "服务开始时间", "服务结束时间", "主办律师账号", "协办律师账号", 
        "案件人员(格式:角色|主体类型|姓名|证件号)", "收费方式", "标的额", "应收金额", "已收金额", "收费说明", "委托阶段"
    ]
    writer.writerow(headers)
    
    # 逐行写入案件数据
    for c in cases:
        # 解析律师
        main_lawyer = ""
        co_lawyers = []
        for lw in c.internal_lawyers:
            if lw.role_type == "主办律师" and lw.lawyer:
                main_lawyer = lw.lawyer.username
            elif lw.role_type == "协办律师" and lw.lawyer:
                co_lawyers.append(lw.lawyer.username)
                
        # 解析案件人员 (以分号隔开多个人员，单个人员用 | 分隔属性)
        entities_str = []
        for rel in c.external_relations:
            ent = rel.entity
            entities_str.append(f"{rel.role_name}|{ent.entity_type.value}|{ent.name}|{ent.id_number or ''}")
            
        # 解析详情和财务，防空指针
        dt = c.details
        fin = c.finance

        # 新增查表逻辑：将数字 ID 转为具体的汉字名称
        topic_name = ""
        region_name = ""
        if dt:
            if dt.topic_id:
                t_name = db.query(models.DictionaryTopic.name).filter(models.DictionaryTopic.id == dt.topic_id).scalar()
                if t_name: topic_name = t_name
            if dt.region_id:
                r_name = db.query(models.DictionaryTopic.name).filter(models.DictionaryTopic.id == dt.region_id).scalar()
                if r_name: region_name = r_name
        
        row = [
            c.serial_no, c.case_no or "", c.title, c.case_type.value, c.source.value, 
            c.status.value, c.process_tag.value if c.process_tag else "正常", 
            str(c.reg_date), c.description or "", 
            topic_name,
            region_name,
            dt.agency_names if dt else "", 
            dt.criminal_type if dt else "",
            "是" if dt and dt.is_legal_aid else "否",
            "是" if dt and dt.is_foreign else "否",
            str(dt.service_start) if dt and dt.service_start else "",
            str(dt.service_end) if dt and dt.service_end else "",
            main_lawyer, ",".join(co_lawyers), ";".join(entities_str),
            fin.billing_method if fin else "",
            str(fin.target_amount) if fin else "0.00",
            str(fin.receivable) if fin else "0.00",
            str(fin.received) if fin else "0.00",
            fin.fee_remark if fin else "",
            ",".join([s.stage_tag for s in c.stages])
        ]
        writer.writerow(row)
        
    stream.seek(0)
    return stream

@router.get("/export/{case_id}")
def export_case_csv(case_id: int, db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """单案导出（详情页使用）：重构为调用标准宽表模板"""
    c = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="案件不存在")
    if current_user.role == models.RoleEnum.LAWYER and c.creator_id != current_user.id:
        raise HTTPException(status_code=403, detail="您无权导出他人的案件")

    stream = _generate_csv_stream([c], db)
    encoded_filename = quote(f"案件详情_{c.serial_no}.csv")
    return StreamingResponse(
        iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )

@router.get("/export-batch")
def export_batch_cases(start_date: str = None, end_date: str = None, db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """历史案件批量导出（管理页使用）：支持时间段筛选，仅限风控管理员"""
    if current_user.role == models.RoleEnum.LAWYER:
        raise HTTPException(status_code=403, detail="权限不足，仅风控和管理员可导出历史台账")
        
    query = db.query(models.Case)
    if start_date:
        query = query.filter(models.Case.reg_date >= start_date)
    if end_date:
        query = query.filter(models.Case.reg_date <= end_date)
        
    cases = query.order_by(models.Case.id.desc()).all()
    stream = _generate_csv_stream(cases, db)
    
    encoded_filename = quote(f"历史案件台账_{datetime.now().strftime('%Y%m%d')}.csv")
    return StreamingResponse(
        iter([stream.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename*=utf-8''{encoded_filename}"}
    )


@router.post("/import")
def import_cases_csv(file: UploadFile = File(...), db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """导入历史案件 (完整的 CSV 解析与事务入库逻辑)"""
    # 权限校验
    if current_user.role == models.RoleEnum.LAWYER:
        raise HTTPException(status_code=403, detail="仅风控或管理员可导入数据")
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="请上传 CSV 格式文件")

    # 严格定义必须匹配的表头
    expected_headers = [
        "流水号", "案号", "案件名称", "案件类型", "案件来源", "当前状态", "异常标记", "登记日期", 
        "案件说明", "案由/罪名", "办案机关省市", "办案机关名称", "刑事类型", "是否法律援助", 
        "是否涉外", "服务开始时间", "服务结束时间", "主办律师账号", "协办律师账号", 
        "案件人员(格式:角色|主体类型|姓名|证件号)", "收费方式", "标的额", "应收金额", "已收金额", "收费说明", "委托阶段"
    ]

    try:
        # 读取内容，utf-8-sig 可以自动处理 Excel 生成 CSV 时带的 BOM 头
        content = file.file.read().decode('utf-8-sig')
        stream = io.StringIO(content)
        reader = csv.DictReader(stream)
        
        # 严格核对表头
        if not reader.fieldnames or list(reader.fieldnames) != expected_headers:
            raise ValueError("CSV 模板字段不匹配，请先点击【下载导入模板】获取标准格式！")

        success_count = 0
        skip_count = 0

        # 辅助日期解析函数
        def parse_date(d_str):
            if not d_str or not d_str.strip(): return None
            try:
                return datetime.strptime(d_str.strip(), "%Y-%m-%d").date()
            except ValueError:
                return None

        # 逐行读取并包裹在事务中
        for row_idx, row in enumerate(reader, start=2):
            
            # 查重机制：如果流水号已存在，安全跳过，防止重复导入
            existing_case = db.query(models.Case).filter(models.Case.serial_no == row["流水号"].strip()).first()
            if existing_case:
                skip_count += 1
                continue

            # 插入案件主表 (cases)
            new_case = models.Case(
                serial_no=row["流水号"].strip(),
                case_no=row["案号"].strip() if row["案号"].strip() else None,
                title=row["案件名称"].strip(),
                case_type=row["案件类型"].strip(),
                source=row["案件来源"].strip(),
                status=row["当前状态"].strip(),
                process_tag=row["异常标记"].strip() if row["异常标记"].strip() else "正常",
                reg_date=parse_date(row["登记日期"]) or datetime.now().date(),
                description=row["案件说明"].strip(),
                creator_id=current_user.id
            )
            db.add(new_case)
            db.flush()

            # 新增：根据中文名称反向查找字典 ID
            topic_id = None
            t_name = row["案由/罪名"].strip()
            if t_name:
                t_obj = db.query(models.DictionaryTopic.id).filter(models.DictionaryTopic.name == t_name).first()
                if t_obj: topic_id = t_obj.id

            region_id = None
            r_name = row["办案机关省市"].strip()
            if r_name:
                r_obj = db.query(models.DictionaryTopic.id).filter(models.DictionaryTopic.name == r_name).first()
                if r_obj: region_id = r_obj.id

            # 插入案件详情 (case_details)
            detail = models.CaseDetail(
                case_id=new_case.id,
                topic_id=int(row["案由/罪名ID"]) if row["案由/罪名ID"].strip() else None,
                region_id=int(row["办案机关省市ID"]) if row["办案机关省市ID"].strip() else None,
                agency_names=row["办案机关名称"].strip(),
                criminal_type=row["刑事类型"].strip(),
                is_legal_aid=(row["是否法律援助"].strip() == "是"),
                is_foreign=(row["是否涉外"].strip() == "是"),
                service_start=parse_date(row["服务开始时间"]),
                service_end=parse_date(row["服务结束时间"])
            )
            db.add(detail)

            # 插入财务信息 (case_finances)
            finance = models.CaseFinance(
                case_id=new_case.id,
                billing_method=row["收费方式"].strip(),
                target_amount=Decimal(row["标的额"].strip() or '0.00'),
                receivable=Decimal(row["应收金额"].strip() or '0.00'),
                received=Decimal(row["已收金额"].strip() or '0.00'),
                fee_remark=row["收费说明"].strip()
            )
            db.add(finance)

            # 插入委托阶段 (case_stage_map) 
            stages_str = row["委托阶段"].strip()
            if stages_str:
                for s in stages_str.split(","):
                    if s.strip():
                        db.add(models.CaseStageMap(case_id=new_case.id, stage_tag=s.strip()))

            # 解析案件人员 (核心难点：切割并映射)
            entities_str = row["案件人员(格式:角色|主体类型|姓名|证件号)"].strip()
            if entities_str:
                for ent_item in entities_str.split(";"):
                    if not ent_item.strip(): continue
                    parts = ent_item.split("|")
                    if len(parts) >= 3: # 至少需要角色、类型、姓名
                        role_name = parts[0].strip()
                        ent_type = parts[1].strip()
                        ent_name = parts[2].strip()
                        ent_id_number = parts[3].strip() if len(parts) > 3 else None
                        
                        # 查找主体是否已存在 (优先身份证，其次名称)
                        ee_query = db.query(models.ExternalEntity)
                        ee = None
                        if ent_id_number:
                            ee = ee_query.filter(models.ExternalEntity.id_number == ent_id_number).first()
                        if not ee:
                            ee = ee_query.filter(models.ExternalEntity.name == ent_name).first()
                        
                        # 如果是新人员，插入 external_entities
                        if not ee:
                            ee = models.ExternalEntity(
                                entity_type=ent_type,
                                name=ent_name,
                                id_number=ent_id_number,
                                id_type="身份证" if len(ent_id_number or '') == 18 else "其它"
                            )
                            db.add(ee)
                            db.flush()
                            
                        # 建立关联
                        db.add(models.CaseExternalRelation(case_id=new_case.id, entity_id=ee.id, role_name=role_name))

            # 解析内部律师
            main_l_username = row["主办律师账号"].strip()
            co_l_usernames = [u.strip() for u in row["协办律师账号"].split(",") if u.strip()]
            
            # 匹配主办律师
            if main_l_username:
                main_l = db.query(models.User).filter(models.User.username == main_l_username).first()
                if main_l:
                    db.add(models.CaseInternalLawyer(case_id=new_case.id, lawyer_id=main_l.id, role_type="主办律师"))
            
            # 匹配协办律师
            for co_u in co_l_usernames:
                co_l = db.query(models.User).filter(models.User.username == co_u).first()
                if co_l:
                    db.add(models.CaseInternalLawyer(case_id=new_case.id, lawyer_id=co_l.id, role_type="协办律师"))

            success_count += 1
        db.commit()
        
        msg = f"导入完成！成功入库 {success_count} 条数据。"
        if skip_count > 0:
            msg += f" (检测到 {skip_count} 条流水号重复，已自动跳过)"
        return {"message": msg}

    except ValueError as ve:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        db.rollback()
        # 抛出具体的行号，极大方便运维排错
        error_msg = f"第 {row_idx} 行解析失败，数据格式可能有误。请检查后重试。报错提示: {str(e)}"
        raise HTTPException(status_code=400, detail=error_msg)

@router.delete("/{case_id}")
def delete_case(case_id: int, db: Session = Depends(database.get_db), current_user=Depends(auth.get_current_user)):
    """删除案件（仅管理员账户可见与操作）"""
    if current_user.role != models.RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="权限不足：仅管理员可删除案件")
        
    c = db.query(models.Case).filter(models.Case.id == case_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="案件不存在")
        
    # 为防止外键报错，必须按照子表到主表的顺序依次彻底删除
    db.query(models.CaseDetail).filter(models.CaseDetail.case_id == case_id).delete()
    db.query(models.CaseExternalRelation).filter(models.CaseExternalRelation.case_id == case_id).delete()
    db.query(models.CaseInternalLawyer).filter(models.CaseInternalLawyer.case_id == case_id).delete()
    db.query(models.CaseStageMap).filter(models.CaseStageMap.case_id == case_id).delete()
    db.query(models.CaseFinance).filter(models.CaseFinance.case_id == case_id).delete()
    db.query(models.CaseOperationLog).filter(models.CaseOperationLog.case_id == case_id).delete()
    db.query(models.CaseDocument).filter(models.CaseDocument.case_id == case_id).delete()
    db.delete(c)
    db.commit()
    return {"message": "该案件及其所有底层关联数据已被彻底删除"}