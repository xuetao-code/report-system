from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from app.database import Base


class Report(Base):
    """报表定义表"""
    __tablename__ = "reports"
    
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    dsl_definition = Column(JSON, nullable=False)
    created_by = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DataSource(Base):
    """数据源配置表"""
    __tablename__ = "data_sources"
    
    id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # mysql, postgresql, sqlite
    host = Column(String(255))
    port = Column(Integer)
    database = Column(String(255))
    username = Column(String(255))
    password_encrypted = Column(Text)
    file_path = Column(String(500))  # SQLite 文件路径
    extra_config = Column(JSON)  # 额外配置
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReportPermission(Base):
    """报表权限表"""
    __tablename__ = "report_permissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(64), ForeignKey("reports.id"))
    user_id = Column(String(64), nullable=False)
    permission = Column(String(20))  # view, edit
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ScheduledTask(Base):
    """定时任务表"""
    __tablename__ = "scheduled_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(String(64), ForeignKey("reports.id"))
    cron_expression = Column(String(50))
    recipient_email = Column(String(255))
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ReportShare(Base):
    """报表分享配置表"""
    __tablename__ = "report_shares"
    
    id = Column(String(64), primary_key=True)
    report_id = Column(String(64), nullable=False)
    share_token = Column(String(128), unique=True, nullable=False)
    created_by = Column(String(64))
    created_at = Column(String(50), server_default=func.now())
    expires_at = Column(String(50))
    
    # 权限配置
    access_level = Column(String(20), default='private')
    access_password = Column(String(255))
    
    # 访问控制
    max_views = Column(Integer)
    view_count = Column(Integer, default=0)
    
    # 功能配置
    allow_download = Column(Boolean, default=True)
    allow_refresh = Column(Boolean, default=True)
    refresh_interval = Column(Integer, default=0)
    
    # 样式配置
    theme = Column(String(50), default='default')
    show_header = Column(Boolean, default=True)
    show_footer = Column(Boolean, default=True)
    
    status = Column(String(20), default='active')
    updated_at = Column(String(50), server_default=func.now())


class ReportShareLog(Base):
    """报表访问日志表"""
    __tablename__ = "report_share_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    share_id = Column(String(64), nullable=False, index=True)
    visitor_ip = Column(String(45))
    visitor_ua = Column(Text)
    accessed_at = Column(String(50), server_default=func.now(), index=True)
    params = Column(JSON)
    duration_ms = Column(Integer)
