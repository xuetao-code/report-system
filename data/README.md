# SQLite 测试数据库说明

## 📦 数据库位置

```
/root/.openclaw/workspace/report-system/data/test.db
```

## 📊 数据库结构

### 表结构

#### 1. products（产品表）
| 字段 | 类型 | 说明 |
|------|------|------|
| product_id | TEXT | 产品 ID（主键） |
| product_name | TEXT | 产品名称 |
| category | TEXT | 类别 |
| unit_price | REAL | 单价 |
| stock_qty | INTEGER | 库存数量 |
| created_at | TEXT | 创建日期 |

**数据量**: 8 条记录

#### 2. customers（客户表）
| 字段 | 类型 | 说明 |
|------|------|------|
| customer_id | TEXT | 客户 ID（主键） |
| customer_name | TEXT | 客户姓名 |
| city | TEXT | 城市 |
| email | TEXT | 邮箱 |
| phone | TEXT | 电话 |
| created_at | TEXT | 注册日期 |

**数据量**: 5 条记录

#### 3. orders（订单表）
| 字段 | 类型 | 说明 |
|------|------|------|
| order_id | TEXT | 订单 ID（主键） |
| customer_id | TEXT | 客户 ID（外键） |
| order_date | TEXT | 订单日期 |
| total_amount | REAL | 订单总额 |
| status | TEXT | 订单状态 |

**数据量**: 30 条记录

#### 4. order_items（订单明细表）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 自增 ID（主键） |
| order_id | TEXT | 订单 ID（外键） |
| product_id | TEXT | 产品 ID（外键） |
| quantity | INTEGER | 数量 |
| unit_price | REAL | 单价 |
| amount | REAL | 金额 |

**数据量**: 79 条记录

### 视图

#### v_sales_summary（销售统计视图）
按类别统计销售情况：
- category: 类别
- order_count: 订单数
- total_qty: 销售数量
- total_amount: 销售金额

#### v_customer_stats（客户统计视图）
客户订单统计：
- customer_id: 客户 ID
- customer_name: 客户姓名
- city: 城市
- order_count: 订单数
- total_spent: 总消费

---

## 🔧 在报表系统中使用

### 方式 1：通过前端界面

1. 访问 http://0.0.0.0:3000
2. 点击 **数据源** → **新建数据源**
3. 填写配置：
   ```json
   {
     "名称": "测试数据库",
     "类型": "sqlite",
     "文件路径": "/root/.openclaw/workspace/report-system/data/test.db"
   }
   ```
4. 点击 **测试连接** 验证
5. 点击 **保存**

### 方式 2：通过 API

```bash
curl -X POST http://localhost:8000/api/datasources \
  -H "Content-Type: application/json" \
  -d '{
    "name": "测试数据库",
    "type": "sqlite",
    "file_path": "/root/.openclaw/workspace/report-system/data/test.db"
  }'
```

---

## 📝 示例报表 DSL

### 示例 1：销售统计（按类别）

```json
{
  "dataSource": {
    "type": "sqlite",
    "file_path": "/root/.openclaw/workspace/report-system/data/test.db",
    "query": "SELECT * FROM v_sales_summary ORDER BY total_amount DESC"
  },
  "parameters": [],
  "components": [
    {
      "type": "table",
      "columns": [
        {"field": "category", "label": "类别"},
        {"field": "order_count", "label": "订单数"},
        {"field": "total_qty", "label": "销售数量"},
        {"field": "total_amount", "label": "销售金额", "format": "currency"}
      ]
    }
  ]
}
```

### 示例 2：客户订单排行

```json
{
  "dataSource": {
    "type": "sqlite",
    "file_path": "/root/.openclaw/workspace/report-system/data/test.db",
    "query": "SELECT customer_name, city, order_count, total_spent FROM v_customer_stats ORDER BY total_spent DESC"
  },
  "parameters": [],
  "components": [
    {
      "type": "table",
      "columns": [
        {"field": "customer_name", "label": "客户", "width": 120},
        {"field": "city", "label": "城市", "width": 80},
        {"field": "order_count", "label": "订单数", "width": 80},
        {"field": "total_spent", "label": "总消费", "width": 120, "format": "currency"}
      ]
    }
  ]
}
```

### 示例 3：产品销量分析

```json
{
  "dataSource": {
    "type": "sqlite",
    "file_path": "/root/.openclaw/workspace/report-system/data/test.db",
    "query": "SELECT p.product_name, p.category, SUM(oi.quantity) as total_qty, SUM(oi.amount) as total_amount FROM order_items oi JOIN products p ON oi.product_id = p.product_id GROUP BY p.product_id ORDER BY total_amount DESC LIMIT 10"
  },
  "parameters": [],
  "components": [
    {
      "type": "table",
      "columns": [
        {"field": "product_name", "label": "产品名称", "width": 150},
        {"field": "category", "label": "类别", "width": 100},
        {"field": "total_qty", "label": "销量", "width": 80},
        {"field": "total_amount", "label": "销售额", "width": 120, "format": "currency"}
      ]
    }
  ]
}
```

### 示例 4：月度销售趋势

```json
{
  "dataSource": {
    "type": "sqlite",
    "file_path": "/root/.openclaw/workspace/report-system/data/test.db",
    "query": "SELECT strftime('%Y-%m', order_date) as month, COUNT(*) as order_count, SUM(total_amount) as total_sales FROM orders WHERE status='已完成' GROUP BY month ORDER BY month"
  },
  "parameters": [],
  "components": [
    {
      "type": "table",
      "columns": [
        {"field": "month", "label": "月份", "width": 100},
        {"field": "order_count", "label": "订单数", "width": 80},
        {"field": "total_sales", "label": "销售额", "width": 120, "format": "currency"}
      ]
    }
  ]
}
```

---

## 🔍 常用查询 SQL

```sql
-- 1. 查询所有产品
SELECT * FROM products;

-- 2. 查询已完成的订单
SELECT * FROM orders WHERE status = '已完成';

-- 3. 查询某个客户的订单
SELECT o.*, c.customer_name 
FROM orders o 
JOIN customers c ON o.customer_id = c.customer_id 
WHERE c.customer_id = 'C001';

-- 4. 查询订单明细
SELECT o.order_id, c.customer_name, p.product_name, oi.quantity, oi.amount
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN customers c ON o.customer_id = c.customer_id
JOIN products p ON oi.product_id = p.product_id;

-- 5. 查询库存预警（库存<50）
SELECT product_name, stock_qty FROM products WHERE stock_qty < 50;

-- 6. 查询每个产品的销量
SELECT p.product_name, SUM(oi.quantity) as total_qty
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.product_id
ORDER BY total_qty DESC;
```

---

## 🛠️ 数据库管理

### 查看数据库文件

```bash
ls -lh /root/.openclaw/workspace/report-system/data/test.db
```

### 使用 SQLite 命令行

```bash
# 打开数据库
sqlite3 /root/.openclaw/workspace/report-system/data/test.db

# 查看所有表
.tables

# 查看表结构
.schema products

# 查询数据
SELECT * FROM products LIMIT 5;

# 退出
.quit
```

### 备份数据库

```bash
cp /root/.openclaw/workspace/report-system/data/test.db \
   /root/.openclaw/workspace/report-system/data/test_backup.db
```

### 重置数据库

删除并重新创建：
```bash
rm /root/.openclaw/workspace/report-system/data/test.db
# 然后重新运行建库脚本
```

---

## 📈 数据统计

| 项目 | 数量 |
|------|------|
| 产品 | 8 个 |
| 客户 | 5 个 |
| 订单 | 30 个 |
| 订单明细 | 79 条 |
| 数据库大小 | ~32 KB |

---

**创建时间**: 2026-04-02  
**数据库版本**: v1.0  
**适用系统**: 自定义报表系统 v1.0.0
