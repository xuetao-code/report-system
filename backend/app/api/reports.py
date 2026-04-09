from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import List, Optional
import uuid
from datetime import datetime
import json

from app.database import get_db
from app.models.report import Report
from app.schemas.report import ReportCreate, ReportUpdate, ReportResponse
from app.core.engine import ReportEngine
from sqlalchemy.orm import Session

router = APIRouter()
engine = ReportEngine()


@router.get("", response_model=List[ReportResponse])
async def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """获取报表列表"""
    reports = db.query(Report).offset(skip).limit(limit).all()
    return reports


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str, db: Session = Depends(get_db)):
    """获取单个报表详情"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")
    return report


@router.post("", response_model=ReportResponse)
async def create_report(report_data: ReportCreate, db: Session = Depends(get_db)):
    """创建新报表"""
    report = Report(
        id=str(uuid.uuid4()),
        name=report_data.name,
        description=report_data.description,
        dsl_definition=report_data.dsl_definition,
        created_by=report_data.created_by
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.put("/{report_id}", response_model=ReportResponse)
async def update_report(
    report_id: str,
    report_data: ReportUpdate,
    db: Session = Depends(get_db)
):
    """更新报表"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")
    
    if report_data.name is not None:
        report.name = report_data.name
    if report_data.description is not None:
        report.description = report_data.description
    if report_data.dsl_definition is not None:
        report.dsl_definition = report_data.dsl_definition
    
    report.updated_at = datetime.now()
    db.commit()
    db.refresh(report)
    return report


@router.delete("/{report_id}")
async def delete_report(report_id: str, db: Session = Depends(get_db)):
    """删除报表"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")
    db.delete(report)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{report_id}/preview")
async def preview_report(request: Request, report_id: str, db: Session = Depends(get_db)):
    """预览报表数据（支持参数）"""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")
    
    # 解析请求体
    body = await request.json()
    params = body.get('params', {})
    
    # 解析 DSL
    dsl_definition = report.dsl_definition
    if isinstance(dsl_definition, str):
        dsl_definition = json.loads(dsl_definition)
    
    try:
        # 执行查询
        result = engine.execute_report(dsl_definition, params)
        return result
    except Exception as e:
        logger.error(f"预览报表失败：{e}")
        raise HTTPException(status_code=500, detail=f"查询执行失败：{str(e)}")
