# 自定义报表系统 - 用户手册

## 📖 目录

1. [快速开始](#快速开始)
2. [数据源管理](#数据源管理)
3. [报表设计](#报表设计)
4. [报表导出](#报表导出)
5. [DSL 语法参考](#dsl-语法参考)
6. [常见问题](#常见问题)

---

## 🚀 快速开始

### 1. 访问系统

打开浏览器访问：http://0.0.0.0:3000

### 2. 系统界面

左侧导航栏包含两个主要功能：
- **报表管理** - 创建、查看、导出报表
- **数据源** - 配置数据库连接

---

## 💾 数据源管理

### 添加 SQLite 数据源（推荐新手）

1. 点击左侧菜单 **数据源**
2. 点击 **新建数据源** 按钮
3. 填写配置：

```json
{
  "名称": "本地数据库",
  "类型": "sqlite",
  "文件路径": "/data/mydb.db"
}
```

**提示：**
- 使用 `:memory:` 创建内存数据库（测试用）
- 文件路径使用绝对路径
- SQLite 无需用户名密码

### 添加 MySQL 数据源

```json
{
  "名称": "生产数据库",
  "类型": "mysql",
  "主机": "192.168.1.100",
  "端口": 3306,
  "数据库": "sales_db",
  "用户名": "report_user",
  "密码": "your_password"
}
```

### 添加 PostgreSQL 数据源

```json
{
  "名称": "分析数据库",
  "类型": "postgresql",
  "主机": "192.168.1.101",
  "端口": 5432,
  "数据库": "analytics",
  "用户名": "pg_user",
  "密码": "your_password"
}
```

### 测试连接

点击数据源列表中的 **测试连接** 按钮，验证配置是否正确。

---

## 📊 报表设计

### 创建第一个报表

1. 点击左侧菜单 **报表管理**
2. 点击 **新建报表** 按钮
3. 填写基本信息：
   - **报表名称**：销售日报
   - **描述**：每日销售数据统计

### DSL 定义示例

#### 示例 1：简单表格报表

```json
{
  "dataSource": {
    "type": "sqlite",
    "file_path": "/data/sales.db",
    "query": "SELECT * FROM orders WHERE date >= '${start_date}'"
  },
  "parameters": [
    {
      "name": "start_date",
      "type": "date",
      "default": "2026-01-01",
      "label": "开始日期"
    }
  ],
  "components": [
    {
      "type": "table",
      "columns": [
        {"field": "order_id", "label": "订单号", "width": 120},
        {"field": "customer", "label": "客户", "width": 150},
        {"field": "amount", "label": "金额", "width": 100, "format": "currency"},
        {"field": "date", "label": "日期", "width": 120}
      ]
    }
  ]
}
```

#### 示例 2：MySQL 数据源报表

```json
{
  "dataSource": {
    "type": "mysql",
    "query": "SELECT product_name, SUM(quantity) as total_qty, SUM(amount) as total_amount FROM order_items WHERE date BETWEEN '${start_date}' AND '${end_date}' GROUP BY product_name ORDER BY total_amount DESC"
  },
  "parameters": [
    {"name": "start_date", "type": "date", "default": "2026-01-01"},
    {"name": "end_date", "type": "date", "default": "2026-12-31"}
  ],
  "components": [
    {
      "type": "table",
      "columns": [
        {"field": "product_name", "label": "产品名称"},
        {"field": "total_qty", "label": "销售数量"},
        {"field": "total_amount", "label": "销售金额", "format": "currency"}
      ]
    }
  ]
}
```

#### 示例 3：带统计的报表

```json
{
  "dataSource": {
    "type": "sqlite",
    "file_path": "/data/hr.db",
    "query": "SELECT department, COUNT(*) as emp_count, AVG(salary) as avg_salary FROM employees GROUP BY department"
  },
  "parameters": [],
  "components": [
    {
      "type": "table",
      "columns": [
        {"field": "department", "label": "部门"},
        {"field": "emp_count", "label": "人数"},
        {"field": "avg_salary", "label": "平均工资", "format": "currency"}
      ]
    }
  ]
}
```

---

## 📤 报表导出

### 预览报表

1. 在报表列表中点击 **预览** 按钮
2. 查看查询结果（JSON 格式）
3. 可在控制台查看详细数据

### 导出 Excel

1. 点击 **导出 Excel** 按钮
2. 浏览器自动下载 `.xlsx` 文件
3. 文件包含格式化的表格数据

### 导出 PDF

1. 点击 **导出 PDF** 按钮
2. 浏览器自动下载 `.pdf` 文件
3. PDF 包含标题和格式化表格

---

## 📝 DSL 语法参考

### 根结构

```json
{
  "dataSource": { ... },
  "parameters": [ ... ],
  "components": [ ... ]
}
```

### dataSource 配置

#### SQLite
```json
{
  "type": "sqlite",
  "file_path": "/path/to/database.db",
  "query": "SELECT * FROM table"
}
```

#### MySQL
```json
{
  "type": "mysql",
  "query": "SELECT * FROM table"
}
```

#### PostgreSQL
```json
{
  "type": "postgresql",
  "query": "SELECT * FROM table"
}
```

### parameters 参数

```json
[
  {
    "name": "param_name",
    "type": "date|number|string",
    "default": "default_value",
    "label": "显示标签"
  }
]
```

### components 组件

#### 表格组件
```json
{
  "type": "table",
  "columns": [
    {
      "field": "column_name",
      "label": "列标题",
      "width": 120,
      "format": "currency|number|date"
    }
  ]
}
```

### 支持的格式

| 格式 | 说明 | 示例 |
|------|------|------|
| `currency` | 货币格式 | ¥1,234.56 |
| `number` | 数字格式 | 1,234.56 |
| `date` | 日期格式 | 2026-04-02 |
| `percent` | 百分比 | 12.34% |

---

## ❓ 常见问题

### Q1: SQLite 文件路径怎么写？

**A:** 使用绝对路径，例如：
- Linux/Mac: `/data/mydb.db`
- Windows: `C:/data/mydb.db`

### Q2: 如何创建测试数据？

**A:** 使用 SQLite 命令行：
```bash
sqlite3 /data/test.db << EOF
CREATE TABLE orders (
  order_id TEXT,
  customer TEXT,
  amount REAL,
  date TEXT
);
INSERT INTO orders VALUES ('ORD001', '张三', 100.50, '2026-04-01');
INSERT INTO orders VALUES ('ORD002', '李四', 200.00, '2026-04-02');
EOF
```

### Q3: 报表导出失败怎么办？

**A:** 检查以下几点：
1. DSL 语法是否正确（JSON 格式）
2. 数据源连接是否正常
3. SQL 查询是否能执行
4. 查看浏览器控制台错误信息

### Q4: 支持哪些数据库？

**A:** 
- ✅ SQLite（本地文件）
- ✅ MySQL 5.7+
- ✅ PostgreSQL 10+
- ⏳ ClickHouse（计划中）

### Q5: 如何分享报表？

**A:** 
1. 导出 PDF/Excel 后发送文件
2. 分享报表 DSL 配置
3. 截图分享预览结果

### Q6: 数据安全性如何？

**A:** 
- 数据源密码存储需加密（生产环境）
- 支持行级权限控制（开发中）
- 建议内网部署

---

## 🛠️ 技术支持

### API 文档

访问：http://0.0.0.0:8000/docs

### 健康检查

```bash
curl http://0.0.0.0:8000/health
# 返回：{"status":"healthy"}
```

### 日志查看

```bash
# 后端日志
tail -f /tmp/report_backend.log

# 前端日志
# 浏览器 F12 开发者工具
```

---

## 📚 更多示例

### 销售分析报表

```json
{
  "dataSource": {
    "type": "mysql",
    "query": "SELECT DATE_FORMAT(order_date, '%Y-%m') as month, SUM(amount) as total FROM orders GROUP BY month ORDER BY month DESC LIMIT 12"
  },
  "parameters": [],
  "components": [
    {
      "type": "table",
      "columns": [
        {"field": "month", "label": "月份"},
        {"field": "total", "label": "销售额", "format": "currency"}
      ]
    }
  ]
}
```

### 库存预警报表

```json
{
  "dataSource": {
    "type": "sqlite",
    "file_path": "/data/warehouse.db",
    "query": "SELECT product_name, stock_qty, min_stock FROM products WHERE stock_qty < min_stock"
  },
  "parameters": [],
  "components": [
    {
      "type": "table",
      "columns": [
        {"field": "product_name", "label": "产品名称"},
        {"field": "stock_qty", "label": "当前库存"},
        {"field": "min_stock", "label": "最低库存", "format": "number"}
      ]
    }
  ]
}
```

---

**版本**: v1.0.0  
**更新日期**: 2026-04-02  
**文档地址**: http://0.0.0.0:8000/manual
