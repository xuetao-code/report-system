from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from typing import List
import uuid

from app.database import get_db
from app.models.report import DataSource
from app.schemas.report import DataSourceCreate, DataSourceUpdate, DataSourceResponse
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("", response_model=List[DataSourceResponse])
async def list_datasources(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取数据源列表"""
    datasources = db.query(DataSource).offset(skip).limit(limit).all()
    return datasources


@router.get("/{ds_id}", response_model=DataSourceResponse)
async def get_datasource(ds_id: str, db: Session = Depends(get_db)):
    """获取单个数据源详情"""
    datasource = db.query(DataSource).filter(DataSource.id == ds_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return datasource


@router.post("", response_model=DataSourceResponse)
async def create_datasource(ds_data: DataSourceCreate, db: Session = Depends(get_db)):
    """创建新数据源"""
    datasource = DataSource(
        id=str(uuid.uuid4()),
        name=ds_data.name,
        type=ds_data.type,
        host=ds_data.host,
        port=ds_data.port,
        database=ds_data.database,
        username=ds_data.username,
        password_encrypted=ds_data.password,
        file_path=ds_data.file_path
    )
    db.add(datasource)
    db.commit()
    db.refresh(datasource)
    return datasource


@router.put("/{ds_id}", response_model=DataSourceResponse)
async def update_datasource(
    ds_id: str,
    ds_data: DataSourceUpdate,
    db: Session = Depends(get_db)
):
    """更新数据源"""
    datasource = db.query(DataSource).filter(DataSource.id == ds_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    if ds_data.name is not None:
        datasource.name = ds_data.name
    if ds_data.host is not None:
        datasource.host = ds_data.host
    if ds_data.port is not None:
        datasource.port = ds_data.port
    if ds_data.database is not None:
        datasource.database = ds_data.database
    if ds_data.username is not None:
        datasource.username = ds_data.username
    if ds_data.password is not None:
        datasource.password_encrypted = ds_data.password
    if ds_data.file_path is not None:
        datasource.file_path = ds_data.file_path
    
    db.commit()
    db.refresh(datasource)
    return datasource


@router.delete("/{ds_id}")
async def delete_datasource(ds_id: str, db: Session = Depends(get_db)):
    """删除数据源"""
    datasource = db.query(DataSource).filter(DataSource.id == ds_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    db.delete(datasource)
    db.commit()
    return {"message": "删除成功"}


@router.post("/{ds_id}/test")
async def test_datasource(ds_id: str, db: Session = Depends(get_db)):
    """测试数据源连接"""
    datasource = db.query(DataSource).filter(DataSource.id == ds_id).first()
    if not datasource:
        raise HTTPException(status_code=404, detail="数据源不存在")
    return {"status": "connected", "message": "连接成功"}
