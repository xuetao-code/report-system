# 报表系统后续功能设计方案

## 📋 需求概述

### 功能 1: 报表单独发布
- 每个报表生成独立的访问链接
- 支持公开访问或权限控制
- 支持嵌入第三方系统（iframe）
- 支持定时刷新数据

### 功能 2: 可视化报表设计器
- 空白报表创建
- 可视化选择数据源
- 拖拽式指标选择
- 实时预览效果

---

## 🎯 功能 1: 报表单独发布

### 1.1 功能设计

#### 访问模式
```
1. 公开链接：http://0.0.0.0:8000/report/{share_id}
2. 嵌入链接：http://0.0.0.0:8000/report/{share_id}?embed=true
3. 带参数链接：http://0.0.0.0:8000/report/{share_id}?start_date=2026-01-01
```

#### 权限控制
| 权限级别 | 说明 | 访问方式 |
|---------|------|---------|
| **私有** | 仅创建者可访问 | 需要登录 |
| **组织内** | 同组织成员可访问 | 需要登录 + 组织验证 |
| **公开** | 任何人可访问 | 无需登录 |
| **密码保护** | 输入密码访问 | 密码验证 |

### 1.2 数据库设计

```sql
-- 报表分享配置表
CREATE TABLE report_shares (
    id VARCHAR(64) PRIMARY KEY,
    report_id VARCHAR(64) NOT NULL,
    share_token VARCHAR(128) UNIQUE NOT NULL,  -- 分享令牌
    created_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,  -- 过期时间（NULL 为永久）
    
    -- 权限配置
    access_level VARCHAR(20) DEFAULT 'private',  -- private/org/public/password
    access_password VARCHAR(255),  -- 加密存储
    
    -- 访问控制
    max_views INTEGER,  -- 最大访问次数（NULL 为不限）
    view_count INTEGER DEFAULT 0,
    
    -- 功能配置
    allow_download BOOLEAN DEFAULT TRUE,  -- 允许下载
    allow_refresh BOOLEAN DEFAULT TRUE,   -- 允许刷新
    refresh_interval INTEGER DEFAULT 0,   -- 自动刷新间隔（秒，0 为不刷新）
    
    -- 样式配置
    theme VARCHAR(50) DEFAULT 'default',  -- 主题
    show_header BOOLEAN DEFAULT TRUE,     -- 显示头部
    show_footer BOOLEAN DEFAULT TRUE,     -- 显示底部
    
    status VARCHAR(20) DEFAULT 'active',  -- active/inactive/expired
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 报表访问日志表
CREATE TABLE report_share_logs (
    id SERIAL PRIMARY KEY,
    share_id VARCHAR(64) NOT NULL,
    visitor_ip VARCHAR(45),
    visitor_ua TEXT,
    accessed_at TIMESTAMP DEFAULT NOW(),
    params JSONB,  -- 访问参数
    duration_ms INTEGER  -- 访问时长
);

-- 索引
CREATE INDEX idx_report_shares_token ON report_shares(share_token);
CREATE INDEX idx_report_shares_report_id ON report_shares(report_id);
CREATE INDEX idx_report_logs_share_id ON report_share_logs(share_id);
```

### 1.3 API 设计

```python
# 创建分享链接
POST /api/reports/{report_id}/share
Request:
{
    "access_level": "public",  # private/org/public/password
    "expires_days": 30,        # 过期天数（NULL 为永久）
    "allow_download": True,
    "refresh_interval": 300,   # 5 分钟刷新
    "theme": "default"
}
Response:
{
    "share_id": "xxx",
    "share_token": "xxx",
    "share_url": "http://0.0.0.0:8000/report/xxx",
    "embed_url": "http://0.0.0.0:8000/report/xxx?embed=true",
    "expires_at": "2026-05-02T00:00:00"
}

# 更新分享配置
PUT /api/shares/{share_id}

# 删除分享链接
DELETE /api/shares/{share_id}

# 获取分享统计
GET /api/shares/{share_id}/stats
Response:
{
    "view_count": 123,
    "unique_visitors": 45,
    "last_accessed": "2026-04-02T23:00:00"
}

# 公开访问报表（无需登录）
GET /report/{share_token}
GET /report/{share_token}?embed=true
GET /report/{share_token}?start_date=2026-01-01

# 验证密码（如果需要）
POST /api/shares/{share_token}/verify
{
    "password": "xxx"
}
```

### 1.4 前端页面设计

#### 独立报表页面结构
```vue
<!-- /report/[share_token].vue -->
<template>
  <div class="report-standalone" :class="{ 'embed-mode': isEmbed }">
    <!-- 头部（可配置显示/隐藏） -->
    <header v-if="config.show_header">
      <h1>{{ report.name }}</h1>
      <div class="header-actions">
        <el-button v-if="config.allow_download" @click="download">下载</el-button>
        <el-button v-if="config.allow_refresh" @click="refresh">刷新</el-button>
        <span class="last-update">最后更新：{{ lastUpdate }}</span>
      </div>
    </header>
    
    <!-- 报表内容 -->
    <main>
      <component 
        v-for="comp in components" 
        :key="comp.id"
        :is="getComponentType(comp.type)"
        :data="comp.data"
        :config="comp.config"
      />
    </main>
    
    <!-- 底部（可配置显示/隐藏） -->
    <footer v-if="config.show_footer">
      <p>Powered by 自定义报表系统</p>
    </footer>
    
    <!-- 密码验证弹窗 -->
    <el-dialog v-model="showPasswordDialog" title="访问验证">
      <el-input v-model="password" type="password" placeholder="请输入访问密码" />
      <template #footer>
        <el-button type="primary" @click="verifyPassword">验证</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
// 自动刷新
let refreshTimer = null
if (config.refresh_interval > 0) {
  refreshTimer = setInterval(refresh, config.refresh_interval * 1000)
}

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.report-standalone {
  min-height: 100vh;
  background: #f5f7fa;
}

/* 嵌入模式：去除边距和背景 */
.report-standalone.embed-mode {
  background: transparent;
}

.report-standalone.embed-mode header,
.report-standalone.embed-mode footer {
  display: none;
}
</style>
```

### 1.5 安全考虑

```python
# 分享令牌生成
import secrets
import hashlib

def generate_share_token():
    """生成安全的分享令牌"""
    return secrets.token_urlsafe(32)

# 密码验证
from passlib.hash import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.verify(password, hashed)

# 访问频率限制
from fastapi_limiter.depends import RateLimiter

@router.get("/report/{share_token}")
async def view_report(
    share_token: str,
    request: Request,
    # 限制每个 IP 每分钟最多 60 次访问
    limited = Depends(RateLimiter(times=60, minutes=1))
):
    pass

# 令牌过期检查
def is_share_expired(share: ReportShare) -> bool:
    if share.expires_at and share.expires_at < datetime.now():
        return True
    if share.max_views and share.view_count >= share.max_views:
        return True
    return False
```

---

## 🎨 功能 2: 可视化报表设计器

### 2.1 功能设计

#### 设计器界面布局
```
┌─────────────────────────────────────────────────────────┐
│  🎨 报表设计器                          [保存] [预览] [取消] │
├──────────────┬──────────────────────────────────────────┤
│              │                                          │
│  数据源列表   │           画布区域                        │
│  ──────────  │         (拖拽布局)                        │
│  ▶ MySQL     │  ┌─────────────┐  ┌─────────────┐       │
│  ▶ SQLite    │  │  指标卡组件  │  │  表格组件    │       │
│  ▶ PG        │  │  📊 总订单   │  │  日期 | 金额 │       │
│              │  │  💰 销售额   │  │  04-01|1000 │       │
│  指标/字段    │  └─────────────┘  └─────────────┘       │
│  ──────────  │                                          │
│  📊 订单数    │  ┌─────────────┐  ┌─────────────┐       │
│  💰 销售额    │  │  折线图组件  │  │  饼图组件    │       │
│  📈 利润率    │  │  月度趋势    │  │  类别占比    │       │
│  👥 客户数    │  └─────────────┘  └─────────────┘       │
│              │                                          │
│  图表类型    │                                          │
│  ──────────  │                                          │
│  📊 指标卡    │                                          │
│  📈 折线图    │                                          │
│  📊 柱状图    │                                          │
│  🥧 饼图      │                                          │
│  📋 表格      │                                          │
└──────────────┴──────────────────────────────────────────┘
```

### 2.2 数据库设计

```sql
-- 报表设计草稿表
CREATE TABLE report_drafts (
    id VARCHAR(64) PRIMARY KEY,
    report_id VARCHAR(64),  -- 关联的报表 ID（NULL 表示新报表）
    created_by VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- 设计器状态
    draft_data JSONB NOT NULL,  -- 完整的设计器状态
    
    -- 数据源配置
    selected_datasource_id VARCHAR(64),
    datasource_tables JSONB,  -- 已加载的表结构
    selected_fields JSONB,    -- 已选择的字段
    
    -- 组件配置
    components JSONB,  -- 组件列表及配置
    
    -- 布局配置
    layout_config JSONB,  -- 网格布局配置
    
    status VARCHAR(20) DEFAULT 'draft',  -- draft/published/archived
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 数据源元数据缓存表
CREATE TABLE datasource_metadata (
    id VARCHAR(64) PRIMARY KEY,
    datasource_id VARCHAR(64) NOT NULL,
    fetched_at TIMESTAMP DEFAULT NOW(),
    
    -- 表结构
    tables JSONB NOT NULL,  -- [{name, columns: [{name, type}]}]
    
    -- 指标建议
    recommended_metrics JSONB,  -- 推荐的指标
    
    expires_at TIMESTAMP
);

-- 组件模板表
CREATE TABLE component_templates (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50),  -- card/chart/table
    template JSONB NOT NULL,  -- 组件模板
    preview_image VARCHAR(255),
    usage_count INTEGER DEFAULT 0,
    created_by VARCHAR(64),
    is_public BOOLEAN DEFAULT FALSE
);
```

### 2.3 数据源连接器

```python
class DataSourceConnector:
    """数据源连接器 - 获取元数据"""
    
    def __init__(self, datasource_config: dict):
        self.config = datasource_config
        self.engine = self._create_engine()
    
    def get_tables(self) -> list:
        """获取所有表"""
        from sqlalchemy import inspect
        inspector = inspect(self.engine)
        return inspector.get_table_names()
    
    def get_table_columns(self, table_name: str) -> list:
        """获取表字段"""
        from sqlalchemy import inspect
        inspector = inspect(self.engine)
        columns = inspector.get_columns(table_name)
        return [
            {
                'name': col['name'],
                'type': str(col['type']),
                'nullable': col['nullable'],
                'is_primary': col.get('primary_key', False)
            }
            for col in columns
        ]
    
    def get_sample_data(self, table_name: str, limit: int = 10) -> list:
        """获取示例数据"""
        from sqlalchemy import text
        with self.engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT * FROM {table_name} LIMIT {limit}")
            )
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result]
    
    def get_recommended_metrics(self, table_name: str) -> list:
        """推荐指标"""
        columns = self.get_table_columns(table_name)
        metrics = []
        
        for col in columns:
            col_type = col['type'].lower()
            col_name = col['name']
            
            # 数值字段：推荐 SUM/AVG
            if any(t in col_type for t in ['int', 'decimal', 'numeric', 'float']):
                metrics.append({
                    'field': col_name,
                    'label': f'{col_name} 总和',
                    'aggregation': 'SUM'
                })
                metrics.append({
                    'field': col_name,
                    'label': f'{col_name} 平均',
                    'aggregation': 'AVG'
                })
            
            # 日期字段：推荐按时间分组
            if 'date' in col_type or 'time' in col_type:
                metrics.append({
                    'field': col_name,
                    'label': f'按{col_name}分组',
                    'aggregation': 'GROUP_BY_DATE'
                })
        
        # 计数指标
        metrics.append({
            'field': '*',
            'label': '记录数',
            'aggregation': 'COUNT'
        })
        
        return metrics
```

### 2.4 前端设计器组件

```vue
<!-- ReportDesigner.vue -->
<template>
  <div class="report-designer">
    <!-- 顶部工具栏 -->
    <div class="designer-toolbar">
      <el-button @click="save">💾 保存</el-button>
      <el-button @click="preview">👁️ 预览</el-button>
      <el-button @click="publish">🚀 发布</el-button>
    </div>
    
    <div class="designer-content">
      <!-- 左侧面板 -->
      <div class="left-panel">
        <!-- 数据源选择 -->
        <el-collapse v-model="activePanels">
          <el-collapse-item title="📊 数据源" name="datasource">
            <el-select v-model="selectedDatasource" @change="loadDatasourceMetadata">
              <el-option 
                v-for="ds in datasources" 
                :key="ds.id" 
                :label="ds.name" 
                :value="ds.id" 
              />
            </el-select>
          </el-collapse-item>
          
          <!-- 表/字段选择 -->
          <el-collapse-item title="📋 数据表" name="tables">
            <el-tree
              :data="tableFields"
              :props="{ label: 'name', children: 'columns' }"
              @node-click="handleFieldSelect"
            />
          </el-collapse-item>
          
          <!-- 推荐指标 -->
          <el-collapse-item title="💡 推荐指标" name="metrics">
            <draggable 
              v-model="recommendedMetrics"
              :sort="false"
              group="metrics"
            >
              <div 
                v-for="metric in recommendedMetrics" 
                :key="metric.field"
                class="metric-item"
              >
                {{ metric.label }}
              </div>
            </draggable>
          </el-collapse-item>
          
          <!-- 图表类型 -->
          <el-collapse-item title="📈 图表类型" name="charts">
            <draggable 
              v-model="chartTypes"
              :sort="false"
              group="components"
            >
              <div 
                v-for="chart in chartTypes" 
                :key="chart.type"
                class="chart-item"
              >
                {{ chart.icon }} {{ chart.name }}
              </div>
            </draggable>
          </el-collapse-item>
        </el-collapse>
      </div>
      
      <!-- 画布区域 -->
      <div class="canvas-area">
        <grid-layout
          v-model="layout"
          :col-num="12"
          :row-height="100"
          :vertical-compact="true"
        >
          <grid-item
            v-for="item in components"
            :key="item.id"
            :x="item.x"
            :y="item.y"
            :w="item.w"
            :h="item.h"
            :i="item.id"
            class="component-item"
          >
            <!-- 组件内容 -->
            <component-renderer 
              :component="item"
              @edit="editComponent"
              @delete="deleteComponent"
            />
          </grid-item>
        </grid-layout>
      </div>
      
      <!-- 右侧属性面板 -->
      <div class="right-panel" v-if="selectedComponent">
        <component-properties 
          :component="selectedComponent"
          @update="updateComponent"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import draggable from 'vuedraggable'
import { GridLayout, GridItem } from 'vue-grid-layout'

// 状态
const selectedDatasource = ref('')
const tableFields = ref([])
const recommendedMetrics = ref([])
const components = ref([])
const layout = ref([])
const selectedComponent = ref(null)

// 加载数据源元数据
async function loadDatasourceMetadata() {
  const res = await api.get(`/datasources/${selectedDatasource.value}/metadata`)
  tableFields.value = res.data.tables.map(table => ({
    name: table.name,
    columns: table.columns
  }))
  
  // 加载推荐指标
  recommendedMetrics.value = res.data.recommended_metrics
}

// 处理字段选择
function handleFieldSelect(data) {
  // 添加到组件或生成查询
}

// 保存报表
async function save() {
  const draft = {
    datasource_id: selectedDatasource.value,
    components: components.value,
    layout: layout.value
  }
  await api.post('/reports/drafts', draft)
}

// 发布报表
async function publish() {
  const report = {
    name: reportName.value,
    dsl_definition: generateDSL()
  }
  await api.post('/reports', report)
}

// 生成 DSL
function generateDSL() {
  return {
    dataSource: {
      type: datasourceType.value,
      query: buildQuery()
    },
    components: components.value.map(comp => ({
      type: comp.type,
      config: comp.config,
      columns: comp.columns
    }))
  }
}
</script>

<style scoped>
.report-designer {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.designer-content {
  flex: 1;
  display: grid;
  grid-template-columns: 250px 1fr 300px;
  overflow: hidden;
}

.left-panel, .right-panel {
  background: #f5f7fa;
  border-right: 1px solid #e6e6e6;
  overflow-y: auto;
}

.canvas-area {
  background: #fff;
  padding: 20px;
  overflow: auto;
}

.metric-item, .chart-item {
  padding: 8px 12px;
  background: white;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  margin-bottom: 8px;
  cursor: move;
}

.metric-item:hover, .chart-item:hover {
  border-color: #409EFF;
  background: #ecf5ff;
}
</style>
```

### 2.5 SQL 生成器

```python
class QueryBuilder:
    """可视化 SQL 生成器"""
    
    def __init__(self, datasource_type: str):
        self.datasource_type = datasource_type
        self.select_fields = []
        self.where_conditions = []
        self.group_by_fields = []
        self.order_by_fields = []
        self.limit = None
    
    def add_field(self, field: str, aggregation: str = None, alias: str = None):
        """添加字段"""
        if aggregation:
            expr = f"{aggregation}({field})"
        else:
            expr = field
        
        if alias:
            expr = f"{expr} AS {alias}"
        
        self.select_fields.append(expr)
        return self
    
    def add_condition(self, field: str, operator: str, value: any):
        """添加条件"""
        if isinstance(value, str):
            value = f"'{value}'"
        self.where_conditions.append(f"{field} {operator} {value}")
        return self
    
    def add_group_by(self, field: str):
        """添加分组"""
        self.group_by_fields.append(field)
        return self
    
    def add_order_by(self, field: str, direction: str = 'ASC'):
        """添加排序"""
        self.order_by_fields.append(f"{field} {direction}")
        return self
    
    def set_limit(self, limit: int):
        """设置限制"""
        self.limit = limit
        return self
    
    def build(self) -> str:
        """构建 SQL"""
        parts = []
        
        # SELECT
        select_part = "SELECT " + ", ".join(self.select_fields)
        parts.append(select_part)
        
        # FROM (需要外部传入表名)
        # parts.append(f"FROM {table_name}")
        
        # WHERE
        if self.where_conditions:
            parts.append("WHERE " + " AND ".join(self.where_conditions))
        
        # GROUP BY
        if self.group_by_fields:
            parts.append("GROUP BY " + ", ".join(self.group_by_fields))
        
        # ORDER BY
        if self.order_by_fields:
            parts.append("ORDER BY " + ", ".join(self.order_by_fields))
        
        # LIMIT
        if self.limit:
            parts.append(f"LIMIT {self.limit}")
        
        return " ".join(parts)


# 使用示例
query = (QueryBuilder('mysql')
    .add_field('date', None, '月份')
    .add_field('amount', 'SUM', '总销售额')
    .add_field('order_id', 'COUNT', '订单数')
    .add_condition('status', '=', '已完成')
    .add_group_by('date')
    .add_order_by('总销售额', 'DESC')
    .set_limit(100)
    .build())

# 输出:
# SELECT date AS 月份，SUM(amount) AS 总销售额，COUNT(order_id) AS 订单数
# WHERE status = '已完成'
# GROUP BY date
# ORDER BY 总销售额 DESC
# LIMIT 100
```

---

## 📅 实施计划

### 阶段一：报表发布功能（2 周）
- [ ] 数据库表设计
- [ ] 分享令牌生成
- [ ] 公开访问 API
- [ ] 独立报表页面
- [ ] 嵌入模式支持

### 阶段二：可视化设计器基础（3 周）
- [ ] 设计器界面框架
- [ ] 数据源元数据获取
- [ ] 拖拽布局组件
- [ ] 组件配置面板
- [ ] SQL 生成器

### 阶段三：设计器高级功能（2 周）
- [ ] 实时预览
- [ ] 指标推荐
- [ ] 模板库
- [ ] 草稿保存
- [ ] 版本历史

### 阶段四：优化与完善（1 周）
- [ ] 性能优化
- [ ] 权限完善
- [ ] 文档编写
- [ ] 测试覆盖

---

## 🔐 安全考虑

### 报表发布安全
1. **令牌安全**: 使用 cryptographically secure 随机数生成
2. **密码保护**: bcrypt 加密存储
3. **访问限制**: IP 频率限制、访问日志
4. **过期机制**: 自动过期、访问次数限制

### 设计器安全
1. **SQL 注入防护**: 参数化查询、白名单验证
2. **数据源权限**: 只读连接、表级权限控制
3. **操作审计**: 设计操作日志

---

**版本**: v2.0 规划  
**创建日期**: 2026-04-03  
**预计完成**: 2026-04-24
