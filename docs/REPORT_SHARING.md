# 报表单独发布功能说明

## ✅ 功能已实现

### 1. 创建分享链接

**API 端点**: `POST /api/reports/{report_id}/share`

**请求示例**:
```bash
curl -X POST http://localhost:8000/api/reports/{report_id}/share \
  -H "Content-Type: application/json" \
  -d '{
    "access_level": "public",
    "expires_days": 30,
    "allow_download": true,
    "allow_refresh": true,
    "refresh_interval": 300
  }'
```

**响应示例**:
```json
{
    "share_id": "sh_17bcf2e9a78feb61",
    "share_token": "nzu0fi3UlnOje82x7tggAs3CfmIISsg53ChcvaZZdWc",
    "share_url": "/report/nzu0fi3UlnOje82x7tggAs3CfmIISsg53ChcvaZZdWc",
    "embed_url": "/report/nzu0fi3UlnOje82x7tggAs3CfmIISsg53ChcvaZZdWc?embed=true",
    "expires_at": "2026-05-03T00:27:04",
    "access_level": "public"
}
```

### 2. 访问权限级别

| 级别 | 说明 | 访问方式 |
|------|------|---------|
| `private` | 私有 | 需要登录（待实现） |
| `public` | 公开 | 任何人可访问 |
| `password` | 密码保护 | 需要输入密码（待实现） |

### 3. 配置参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `access_level` | string | `private` | 访问权限级别 |
| `expires_days` | int | `null` | 过期天数（null 为永久） |
| `max_views` | int | `null` | 最大访问次数 |
| `allow_download` | bool | `true` | 允许下载 |
| `allow_refresh` | bool | `true` | 允许刷新 |
| `refresh_interval` | int | `0` | 自动刷新间隔（秒） |
| `theme` | string | `default` | 主题 |
| `show_header` | bool | `true` | 显示头部 |
| `show_footer` | bool | `true` | 显示底部 |

### 4. 访问链接

- **独立页面**: `http://0.0.0.0:8000/report/{share_token}`
- **嵌入模式**: `http://0.0.0.0:8000/report/{share_token}?embed=true`
- **带参数**: `http://0.0.0.0:8000/report/{share_token}?start_date=2026-01-01`

### 5. 管理 API

#### 获取分享配置
```bash
GET /api/shares/{share_id}
```

#### 删除分享链接
```bash
DELETE /api/shares/{share_id}
```

#### 获取访问统计
```bash
GET /api/shares/{share_id}/stats
```

**响应示例**:
```json
{
    "view_count": 123,
    "unique_visitors": 45,
    "last_accessed": "2026-04-03T00:00:00"
}
```

---

## 📊 数据库表

### report_shares - 分享配置表
```sql
CREATE TABLE report_shares (
    id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    share_token TEXT UNIQUE NOT NULL,
    created_by TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT,
    access_level TEXT DEFAULT 'private',
    access_password TEXT,
    max_views INTEGER,
    view_count INTEGER DEFAULT 0,
    allow_download INTEGER DEFAULT 1,
    allow_refresh INTEGER DEFAULT 1,
    refresh_interval INTEGER DEFAULT 0,
    theme TEXT DEFAULT 'default',
    show_header INTEGER DEFAULT 1,
    show_footer INTEGER DEFAULT 1,
    status TEXT DEFAULT 'active',
    updated_at TEXT DEFAULT (datetime('now'))
);
```

### report_share_logs - 访问日志表
```sql
CREATE TABLE report_share_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    share_id TEXT NOT NULL,
    visitor_ip TEXT,
    visitor_ua TEXT,
    accessed_at TEXT DEFAULT (datetime('now')),
    params TEXT,
    duration_ms INTEGER
);
```

---

## 🎨 独立报表页面特性

### 1. 响应式布局
- 自适应桌面/移动端
- 网格布局展示多个组件
- 嵌入模式自动隐藏头尾

### 2. 自动刷新
- 可配置刷新间隔
- 显示最后更新时间
- 无需手动刷新

### 3. 下载功能
- 支持 PDF 导出
- 支持 Excel 导出
- 可配置是否允许

### 4. 样式主题
- 默认主题
- 可扩展多主题
- 自定义配色

---

## 🔐 安全特性

### 1. 分享令牌
- 使用 `secrets.token_urlsafe(32)` 生成
-  cryptographically secure
- 难以猜测

### 2. 访问控制
- 过期时间验证
- 访问次数限制
- 状态检查（active/expired/disabled）

### 3. 访问日志
- 记录访问 IP
- 记录 User-Agent
- 记录访问时间
- 记录访问参数

### 4. 密码保护（待实现）
- bcrypt 加密存储
- 密码验证页面
- 验证通过后访问

---

## 📝 使用示例

### 创建公开分享链接
```python
import requests

response = requests.post(
    'http://localhost:8000/api/reports/{report_id}/share',
    json={
        'access_level': 'public',
        'expires_days': 30,
        'allow_download': True,
        'refresh_interval': 300  # 5 分钟自动刷新
    }
)

data = response.json()
print(f"分享链接：{data['share_url']}")
print(f"嵌入链接：{data['embed_url']}")
```

### 嵌入到第三方系统
```html
<!--  iframe 嵌入 -->
<iframe 
    src="http://localhost:8000/report/{share_token}?embed=true"
    width="100%"
    height="800px"
    frameborder="0"
></iframe>
```

### 获取访问统计
```python
response = requests.get(
    f'http://localhost:8000/api/shares/{share_id}/stats'
)
stats = response.json()
print(f"总访问次数：{stats['view_count']}")
print(f"独立访客：{stats['unique_visitors']}")
print(f"最后访问：{stats['last_accessed']}")
```

---

## ⏳ 待实现功能

### 1. 密码保护
- [ ] 密码验证页面
- [ ] 密码加密存储
- [ ] 验证 API

### 2. 组织内分享
- [ ] 组织验证
- [ ] 成员权限检查

### 3. 高级统计
- [ ] 访问趋势图
- [ ] 访客地域分布
- [ ] 热门报表排行

### 4. 下载功能
- [ ] PDF 导出
- [ ] Excel 导出
- [ ] 数据导出 API

### 5. 主题定制
- [ ] 多主题支持
- [ ] 自定义配色
- [ ] Logo 上传

---

## 🐛 已知问题

1. **SQLite DateTime**: 已修复，使用 TEXT 类型存储
2. **路由前缀**: 已修复，公开访问路由不需要 `/api` 前缀

---

**版本**: v2.0  
**实现日期**: 2026-04-03  
**状态**: ✅ 已完成
