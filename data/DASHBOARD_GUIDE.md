# 销售分析仪表板 - 复杂报表示例

## 📊 报表概述

这是一个包含多个图表组件的综合销售分析仪表板，展示了完整的报表设计能力。

### 包含组件

| 组件 ID | 类型 | 标题 | 说明 |
|--------|------|------|------|
| **summary_cards** | 指标卡 | 📊 核心指标 | 4 个关键业务指标 |
| **chart_monthly_trend** | 折线图 | 📈 月度销售趋势 | 销售趋势分析 |
| **chart_product_ranking** | 柱状图 | 🏆 产品销售排行 | TOP10 产品排名 |
| **chart_category_share** | 饼图 | 📊 类别销售占比 | 各类别占比 |
| **chart_order_status** | 饼图 | 📋 订单状态分布 | 订单状态统计 |
| **table_customer_value** | 表格 | 💎 客户价值分析 | 客户消费数据 |

---

## 🎨 布局设计

```
┌─────────────────────────────────────────────────────────┐
│  📊 核心指标（4 个指标卡）                                │
│  [📦 总订单] [💰 总销售额] [👤 客单价] [👥 客户数]        │
├──────────────────────────────┬──────────────────────────┤
│  📈 月度销售趋势（折线图）    │  📊 类别销售占比（饼图）  │
│                              │                          │
├──────────────────────────────┼──────────────────────────┤
│  🏆 产品销售排行（柱状图）    │  📋 订单状态分布（饼图）  │
│                              │                          │
├──────────────────────────────┴──────────────────────────┤
│  💎 客户价值分析（明细表格）                             │
│  客户 | 城市 | 订单数 | 总消费 | 客单价 | 最近订单      │
└─────────────────────────────────────────────────────────┘
```

---

## 📝 DSL 配置说明

### 1. 核心指标卡片

```json
{
  "id": "summary_cards",
  "type": "cards",
  "dataSource": {
    "query": "SELECT COUNT(DISTINCT order_id) as total_orders, SUM(total_amount) as total_revenue, AVG(total_amount) as avg_order, COUNT(DISTINCT customer_id) as total_customers FROM orders WHERE status = '已完成'"
  },
  "cards": [
    {"field": "total_orders", "label": "总订单数", "prefix": "📦", "suffix": "单"},
    {"field": "total_revenue", "label": "总销售额", "prefix": "💰", "format": "currency"},
    {"field": "avg_order", "label": "客单价", "prefix": "👤", "format": "currency"},
    {"field": "total_customers", "label": "客户数", "prefix": "👥", "suffix": "人"}
  ]
}
```

**效果：**
```
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ 📦 总订单数  │ 💰 总销售额  │ 👤 客单价    │ 👥 客户数    │
│    25 单     │ ¥327,971.00 │ ¥13,118.84  │    5 人     │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

---

### 2. 折线图 - 月度销售趋势

```json
{
  "id": "chart_monthly_trend",
  "type": "line",
  "title": "📈 月度销售趋势",
  "dataSource": {
    "query": "SELECT month, order_count, total_sales, avg_order_value FROM v_monthly_trend"
  },
  "config": {
    "xField": "month",
    "yFields": ["total_sales"],
    "smooth": true,
    "areaStyle": {"opacity": 0.3},
    "point": {"size": 5, "shape": "circle"},
    "lineStyle": {"width": 3}
  }
}
```

**配置说明：**
- `smooth: true` - 平滑曲线
- `areaStyle` - 曲线下面积填充
- `point` - 数据点样式

---

### 3. 柱状图 - 产品销售排行

```json
{
  "id": "chart_product_ranking",
  "type": "bar",
  "title": "🏆 产品销售排行 TOP10",
  "dataSource": {
    "query": "SELECT product_name, category, total_qty, total_amount FROM v_product_ranking LIMIT 10"
  },
  "config": {
    "xField": "product_name",
    "yField": "total_amount",
    "seriesField": "category",
    "barWidthRatio": 0.6,
    "label": {
      "position": "right",
      "formatter": "(v) => '¥' + v.toLocaleString()"
    }
  }
}
```

**配置说明：**
- `seriesField` - 按类别分组着色
- `label` - 柱子上显示数值标签

---

### 4. 饼图 - 类别销售占比

```json
{
  "id": "chart_category_share",
  "type": "pie",
  "title": "📊 类别销售占比",
  "dataSource": {
    "query": "SELECT category, total_amount, percentage FROM v_category_share"
  },
  "config": {
    "angleField": "total_amount",
    "colorField": "category",
    "radius": 0.8,
    "innerRadius": 0.5,
    "label": {
      "type": "outer",
      "formatter": "{name}: {percentage}%"
    },
    "statistic": {
      "title": {"content": "总销售额"},
      "content": {"formatter": "(v) => '¥' + v.value.toLocaleString()"}
    }
  }
}
```

**配置说明：**
- `innerRadius: 0.5` - 环形图（中空）
- `statistic` - 中心显示总计

---

### 5. 饼图 - 订单状态分布

```json
{
  "id": "chart_order_status",
  "type": "pie",
  "title": "📋 订单状态分布",
  "dataSource": {
    "query": "SELECT status, order_count, percentage FROM v_order_status"
  },
  "config": {
    "angleField": "order_count",
    "colorField": "status",
    "radius": 0.7,
    "label": {
      "type": "spider",
      "formatter": "{name}: {percentage}%"
    }
  }
}
```

**配置说明：**
- `label.type: "spider"` - 蜘蛛线标签布局

---

### 6. 表格 - 客户价值分析

```json
{
  "id": "table_customer_value",
  "type": "table",
  "title": "💎 客户价值分析",
  "dataSource": {
    "query": "SELECT customer_name, city, order_count, total_spent, avg_order_value, last_order_date FROM v_customer_value LIMIT 10"
  },
  "columns": [
    {"field": "customer_name", "label": "客户", "width": 120},
    {"field": "city", "label": "城市", "width": 80},
    {"field": "order_count", "label": "订单数", "width": 80},
    {"field": "total_spent", "label": "总消费", "width": 120, "format": "currency"},
    {"field": "avg_order_value", "label": "客单价", "width": 120, "format": "currency"},
    {"field": "last_order_date", "label": "最近订单", "width": 120, "format": "date"}
  ]
}
```

---

## 📊 数据视图说明

### v_monthly_trend - 月度销售趋势
```sql
SELECT 
    strftime('%Y-%m', order_date) as month,
    COUNT(*) as order_count,
    SUM(total_amount) as total_sales,
    AVG(total_amount) as avg_order_value
FROM orders 
WHERE status = '已完成'
GROUP BY strftime('%Y-%m', order_date)
ORDER BY month
```

### v_product_ranking - 产品销售排行
```sql
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    SUM(oi.quantity) as total_qty,
    SUM(oi.amount) as total_amount,
    COUNT(DISTINCT oi.order_id) as order_count
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY total_amount DESC
LIMIT 10
```

### v_category_share - 类别销售占比
```sql
SELECT 
    p.category,
    COUNT(DISTINCT oi.order_id) as order_count,
    SUM(oi.quantity) as total_qty,
    SUM(oi.amount) as total_amount,
    ROUND(SUM(oi.amount) * 100.0 / (SELECT SUM(oi2.amount) FROM order_items oi2), 2) as percentage
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
JOIN orders o ON oi.order_id = o.order_id
WHERE o.status = '已完成'
GROUP BY p.category
ORDER BY total_amount DESC
```

### v_order_status - 订单状态分布
```sql
SELECT 
    status,
    COUNT(*) as order_count,
    SUM(total_amount) as total_amount,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM orders), 2) as percentage
FROM orders
GROUP BY status
ORDER BY order_count DESC
```

### v_customer_value - 客户价值分析
```sql
SELECT 
    c.customer_id,
    c.customer_name,
    c.city,
    COUNT(o.order_id) as order_count,
    SUM(o.total_amount) as total_spent,
    AVG(o.total_amount) as avg_order_value,
    MAX(o.order_date) as last_order_date
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.status = '已完成'
GROUP BY c.customer_id, c.customer_name, c.city
HAVING COUNT(o.order_id) > 0
ORDER BY total_spent DESC
```

---

## 🚀 使用步骤

### 1. 导入报表配置

在前端界面：
1. 点击 **新建报表**
2. 填写基本信息：
   - 名称：销售分析仪表板
   - 描述：包含多个图表的综合销售分析报表
3. 复制 `dashboard_report.json` 的内容到 **DSL 定义** 文本框
4. 点击 **创建**

### 2. 预览报表

1. 在报表列表中找到 "销售分析仪表板"
2. 点击 **预览** 按钮
3. 查看各个图表组件

### 3. 导出数据

1. 点击 **导出 Excel** 下载完整数据
2. 点击 **导出 PDF** 生成报表文档

---

## 📈 预期效果

### 核心指标
- 📦 总订单数：25 单
- 💰 总销售额：¥327,971.00
- 👤 客单价：¥13,118.84
- 👥 客户数：5 人

### 图表展示
- 📈 月度趋势：显示 3 月销售走势
- 🏆 产品排行：笔记本电脑销售额第一
- 📊 类别占比：电子产品占比最高（约 78%）
- 📋 订单状态：已完成订单占 80%

---

## 🎨 扩展建议

### 可添加的图表类型
- 🗺️ **地图** - 各省市销售分布
- 📊 **雷达图** - 产品多维度对比
- 📉 **漏斗图** - 销售转化漏斗
- 📈 **组合图** - 柱状 + 折线混合

### 可添加的功能
- 🔍 **数据筛选** - 按时间/类别/地区筛选
- 🔗 **图表联动** - 点击饼图联动其他图表
- 📱 **移动端适配** - 响应式布局
- 🔄 **自动刷新** - 定时更新数据

---

**版本**: v1.0  
**创建日期**: 2026-04-02  
**数据源**: SQLite 测试数据库  
**适用场景**: 销售分析、业务仪表板、管理报表
