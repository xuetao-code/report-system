# 自定义报表系统

最小化版本的自定义报表系统，支持 MySQL/PostgreSQL/SQLite 数据源，可视化报表设计和导出功能。

## 🚀 快速启动

### 方式一：Docker Compose（推荐）

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

访问：
- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

### 方式二：Conda 部署（推荐用于开发环境）

```bash
# 1. 创建 conda 环境（Python 3.11）
conda create -n report-system python=3.11 -y

# 2. 激活环境
conda activate report-system

# 3. 安装 Node.js（前端依赖）
conda install -c conda-forge nodejs=20 -y

# 4. 安装后端依赖
cd backend
pip install -r requirements.txt

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库连接等配置

# 6. 启动 PostgreSQL（可选，如使用 Docker）
docker run -d --name reports-db \
  -e POSTGRES_DB=reports \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=pass \
  -p 5432:5432 \
  postgres:15-alpine

# 7. 启动后端服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 8. 新终端启动前端
cd ../frontend
npm install
npm run dev
```

**Conda 环境管理：**

```bash
# 导出环境配置
conda env export > environment.yml

# 从配置恢复环境
conda env create -f environment.yml

# 更新依赖
conda env update -f environment.yml --prune

# 删除环境
conda remove -n report-system --all
```

### 方式三：原生 Python 部署

#### 后端启动

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 复制环境变量文件
cp .env.example .env

# 启动 PostgreSQL（如使用 Docker）
docker run -d --name reports-db \
  -e POSTGRES_DB=reports \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=pass \
  -p 5432:5432 \
  postgres:15-alpine

# 启动后端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端启动

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

## 📊 报表 DSL 示例

### MySQL/PostgreSQL

```json
{
  "dataSource": {
    "type": "mysql",
    "query": "SELECT * FROM sales WHERE date >= '${start_date}'"
  },
  "parameters": [
    {"name": "start_date", "type": "date", "default": "2026-01-01"}
  ],
  "components": [
    {
      "type": "table",
      "columns": [
        {"field": "date", "label": "日期"},
        {"field": "product", "label": "产品"},
        {"field": "amount", "label": "金额", "format": "currency"}
      ]
    }
  ]
}
```

### SQLite

```json
{
  "dataSource": {
    "type": "sqlite",
    "file_path": "/data/sales.db",
    "query": "SELECT * FROM orders WHERE date >= '${start_date}'"
  },
  "parameters": [
    {"name": "start_date", "type": "date", "default": "2026-01-01"}
  ],
  "components": [
    {
      "type": "table",
      "columns": [
        {"field": "order_id", "label": "订单号"},
        {"field": "amount", "label": "金额"}
      ]
    }
  ]
}
```

## 📁 项目结构

```
report-system/
├── backend/              # Python 后端
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── core/        # 核心引擎
│   │   ├── models/      # 数据模型
│   │   ├── schemas/     # Pydantic 模式
│   │   └── services/    # 业务服务
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/            # Vue3 前端
│   ├── src/
│   │   ├── api/        # API 客户端
│   │   ├── views/      # 页面组件
│   │   └── router.ts   # 路由配置
│   └── Dockerfile
├── docs/                # 文档
│   └── SQLITE_DATA_SOURCE.md
├── exports/             # 导出文件存储
├── docker-compose.yml
└── README.md
```

## 🔌 支持的数据源

| 类型 | 说明 | 配置难度 |
|------|------|----------|
| **MySQL** | 主流关系型数据库 | ⭐⭐ |
| **PostgreSQL** | 高级关系型数据库 | ⭐⭐ |
| **SQLite** | 本地文件数据库 | ⭐ |

### SQLite 快速配置

```json
{
  "name": "本地数据库",
  "type": "sqlite",
  "file_path": "/data/mydb.db"
}
```

或内存数据库（测试用）：
```json
{
  "name": "测试库",
  "type": "sqlite",
  "file_path": ":memory:"
}
```

详细说明见：[docs/SQLITE_DATA_SOURCE.md](docs/SQLITE_DATA_SOURCE.md)

## 🔧 技术栈

**后端：**
- FastAPI + Python 3.11
- SQLAlchemy 2.0 (异步)
- PostgreSQL (元数据存储)
- APScheduler (定时任务)
- ReportLab (PDF 生成)
- openpyxl (Excel 生成)

**前端：**
- Vue 3 + TypeScript
- Element Plus UI
- ECharts 5 (图表)
- VXE Table (表格)
- Vite (构建工具)

## 📝 API 接口

### 报表管理
- `GET /api/reports` - 获取报表列表
- `POST /api/reports` - 创建报表
- `GET /api/reports/{id}` - 获取报表详情
- `PUT /api/reports/{id}` - 更新报表
- `DELETE /api/reports/{id}` - 删除报表

### 数据源管理
- `GET /api/datasources` - 获取数据源列表
- `POST /api/datasources` - 创建数据源
- `POST /api/datasources/{id}/test` - 测试连接

### 导出服务
- `POST /api/exports/export` - 导出报表（PDF/Excel）
- `GET /api/exports/{id}/preview` - 预览报表数据

## ⚙️ 配置说明

编辑 `backend/.env` 文件：

```env
# 数据库配置
DATABASE_URL=postgresql://user:pass@localhost:5432/reports

# 邮件配置（定时任务用）
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email
SMTP_PASSWORD=your-password
```

## 📅 后续开发计划

- [ ] 可视化报表设计器（拖拽式）
- [ ] 更多图表类型（ECharts 集成）
- [ ] 数据钻取与联动
- [ ] 行级权限控制
- [ ] ClickHouse 数据源支持
- [ ] 企业微信/钉钉推送

---

**版本：** v1.0.0-MVP  
**日期：** 2026-04-02  
**更新：** 2026-04-06 添加 Conda 部署方式支持
