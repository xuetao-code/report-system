from fastapi import APIRouter, Depends, HTTPException, Response
from typing import Optional
import json
import logging

from app.database import get_db
from app.models.report import Report
from app.schemas.report import ExportRequest
from app.core.engine import ReportEngine
from app.core.renderer import Renderer
from sqlalchemy.orm import Session
from urllib.parse import quote

logger = logging.getLogger(__name__)

router = APIRouter()

engine = ReportEngine()
renderer = Renderer()


@router.post("/export")
async def export_report(
    export_data: ExportRequest,
    db: Session = Depends(get_db)
):
    """导出报表为 PDF 或 Excel"""
    report = db.query(Report).filter(Report.id == export_data.report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")
    
    # dsl_definition 可能已经是 dict（SQLAlchemy JSONB 类型）
    dsl_definition = report.dsl_definition
    if isinstance(dsl_definition, str):
        dsl_definition = json.loads(dsl_definition)
    
    components = dsl_definition.get('components', [])
    
    if not components:
        raise HTTPException(status_code=400, detail="报表没有定义组件")
    
    # 使用第一个组件
    component = components[0]
    
    try:
        data = engine.execute_report_for_component(component, export_data.params or {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询执行失败：{str(e)}")
    
    columns = component.get('columns', [])
    
    if export_data.format == "pdf":
        file_bytes = renderer.generate_pdf(data, columns, component.get('title', report.name))
        media_type = "application/pdf"
        filename = f"{report.name}.pdf"
    elif export_data.format == "excel":
        file_bytes = renderer.generate_excel(data, columns, component.get('title', report.name))
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        filename = f"{report.name}.xlsx"
    else:
        raise HTTPException(status_code=400, detail="不支持的导出格式")
    
    encoded_filename = quote(filename)
    
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.get("/{report_id}/preview")
async def preview_report(
    report_id: str,
    params: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """预览报表数据"""
    import json
    
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报表不存在")
    
    param_dict = {}
    if params:
        try:
            param_dict = json.loads(params)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="参数格式错误")
    
    try:
        report_result = engine.execute_report(report.dsl_definition, param_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询执行失败：{str(e)}")
    
    return report_result
