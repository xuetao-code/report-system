-- 报表分享配置表
CREATE TABLE IF NOT EXISTS report_shares (
    id VARCHAR(64) PRIMARY KEY,
    report_id VARCHAR(64) NOT NULL,
    share_token VARCHAR(128) UNIQUE NOT NULL,
    created_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    
    -- 权限配置
    access_level VARCHAR(20) DEFAULT 'private',
    access_password VARCHAR(255),
    
    -- 访问控制
    max_views INTEGER,
    view_count INTEGER DEFAULT 0,
    
    -- 功能配置
    allow_download BOOLEAN DEFAULT TRUE,
    allow_refresh BOOLEAN DEFAULT TRUE,
    refresh_interval INTEGER DEFAULT 0,
    
    -- 样式配置
    theme VARCHAR(50) DEFAULT 'default',
    show_header BOOLEAN DEFAULT TRUE,
    show_footer BOOLEAN DEFAULT TRUE,
    
    status VARCHAR(20) DEFAULT 'active',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 报表访问日志表
CREATE TABLE IF NOT EXISTS report_share_logs (
    id SERIAL PRIMARY KEY,
    share_id VARCHAR(64) NOT NULL,
    visitor_ip VARCHAR(45),
    visitor_ua TEXT,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    params JSONB,
    duration_ms INTEGER
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_report_shares_token ON report_shares(share_token);
CREATE INDEX IF NOT EXISTS idx_report_shares_report_id ON report_shares(report_id);
CREATE INDEX IF NOT EXISTS idx_report_logs_share_id ON report_share_logs(share_id);
CREATE INDEX IF NOT EXISTS idx_report_logs_accessed ON report_share_logs(accessed_at);
