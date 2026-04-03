from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ============ 报表相关 ============

class ReportCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    dsl_definition: Dict[str, Any]
    created_by: Optional[str] = None


class ReportUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dsl_definition: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    dsl_definition: Dict[str, Any]
    created_by: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============ 数据源相关 ============

class DataSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., pattern="^(mysql|postgresql|sqlite)$")
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    file_path: Optional[str] = None  # SQLite 文件路径


class DataSourceUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class DataSourceResponse(BaseModel):
    id: str
    name: str
    type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    file_path: Optional[str] = None  # SQLite 文件路径
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ 导出相关 ============

class ExportRequest(BaseModel):
    report_id: str
    format: str = Field(..., pattern="^(pdf|excel)$")
    params: Optional[Dict[str, Any]] = {}


# ============ 定时任务相关 ============

class ScheduledTaskCreate(BaseModel):
    report_id: str
    cron_expression: str
    recipient_email: str


class ScheduledTaskResponse(BaseModel):
    id: int
    report_id: str
    cron_expression: str
    recipient_email: str
    enabled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============ 报表分享相关 ============

class ReportShareCreate(BaseModel):
    access_level: str = "private"  # private/org/public/password
    expires_days: Optional[int] = None
    max_views: Optional[int] = None
    allow_download: bool = True
    allow_refresh: bool = True
    refresh_interval: int = 0  # 秒，0 为不刷新
    theme: str = "default"
    show_header: bool = True
    show_footer: bool = True


class ReportShareResponse(BaseModel):
    share_id: str
    share_token: str
    share_url: str
    embed_url: str
    expires_at: Optional[datetime] = None
    access_level: str
