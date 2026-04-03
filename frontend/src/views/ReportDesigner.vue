<template>
  <div class="report-designer">
    <!-- 顶部工具栏 -->
    <div class="designer-toolbar">
      <div class="toolbar-left">
        <el-button @click="saveReport" type="primary" size="small">💾 保存</el-button>
        <el-button @click="previewReport" type="success" size="small">👁️ 预览</el-button>
        <el-button @click="backToList" size="small">← 返回</el-button>
      </div>
      <div class="toolbar-center">
        <el-input 
          v-model="reportName" 
          placeholder="请输入报表名称" 
          size="small"
          style="width: 300px"
        />
      </div>
      <div class="toolbar-right">
        <el-tag type="info" size="small">未保存</el-tag>
      </div>
    </div>

    <div class="designer-content">
      <!-- 左侧工具栏 -->
      <div class="left-panel">
        <el-tabs v-model="activeTab" type="border-card" class="designer-tabs">
          <!-- 数据模板 -->
          <el-tab-pane label="📊 数据模板" name="templates">
            <div class="panel-section">
              <div class="section-title">选择数据源</div>
              <el-select v-model="selectedDatasource" placeholder="选择数据源" size="small" style="width: 100%" @change="loadTables">
                <el-option 
                  v-for="ds in datasources" 
                  :key="ds.id" 
                  :label="ds.name" 
                  :value="ds.id" 
                />
              </el-select>
            </div>
            
            <div class="panel-section" v-if="selectedDatasource">
              <div class="section-title">数据表</div>
              <el-tree
                :data="tableList"
                :props="{ label: 'name', children: 'columns' }"
                @node-click="handleTableSelect"
                default-expand-all
              />
            </div>
            
            <div class="panel-section">
              <div class="section-title">预设模板</div>
              <div class="template-list">
                <div 
                  v-for="tpl in templates" 
                  :key="tpl.id"
                  class="template-item"
                  @click="applyTemplate(tpl)"
                >
                  <div class="template-icon">{{ tpl.icon }}</div>
                  <div class="template-name">{{ tpl.name }}</div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 指标选择 -->
          <el-tab-pane label="📈 指标" name="metrics">
            <div class="panel-section">
              <div class="section-title">已选字段</div>
              <div class="selected-fields">
                <el-tag 
                  v-for="field in selectedFields" 
                  :key="field.name"
                  closable
                  @close="removeField(field)"
                  @click="insertField(field)"
                >
                  {{ field.label }}
                </el-tag>
                <el-empty v-if="selectedFields.length === 0" description="点击字段添加" :image-size="60" />
              </div>
            </div>
            
            <div class="panel-section">
              <div class="section-title">聚合函数</div>
              <div class="function-list">
                <el-button 
                  v-for="fn in aggregateFunctions" 
                  :key="fn.value"
                  size="small"
                  @click="applyFunction(fn)"
                >
                  {{ fn.label }}
                </el-button>
              </div>
            </div>
            
            <div class="panel-section">
              <div class="section-title">推荐指标</div>
              <div class="metric-list">
                <div 
                  v-for="metric in recommendedMetrics" 
                  :key="metric.name"
                  class="metric-item"
                  @click="insertMetric(metric)"
                >
                  <div class="metric-icon">{{ metric.icon }}</div>
                  <div class="metric-info">
                    <div class="metric-name">{{ metric.name }}</div>
                    <div class="metric-desc">{{ metric.desc }}</div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 图表选择 -->
          <el-tab-pane label="📉 图表" name="charts">
            <div class="panel-section">
              <div class="section-title">基础图表</div>
              <div class="chart-list">
                <div 
                  v-for="chart in basicCharts" 
                  :key="chart.type"
                  class="chart-item"
                  @click="insertChart(chart)"
                >
                  <div class="chart-icon">{{ chart.icon }}</div>
                  <div class="chart-name">{{ chart.name }}</div>
                </div>
              </div>
            </div>
            
            <div class="panel-section">
              <div class="section-title">高级图表</div>
              <div class="chart-list">
                <div 
                  v-for="chart in advancedCharts" 
                  :key="chart.type"
                  class="chart-item"
                  @click="insertChart(chart)"
                >
                  <div class="chart-icon">{{ chart.icon }}</div>
                  <div class="chart-name">{{ chart.name }}</div>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>

      <!-- 中间编辑区域 -->
      <div class="center-panel">
        <div class="edit-canvas" ref="canvasRef">
          <!-- 空白状态 -->
          <div v-if="components.length === 0" class="empty-canvas">
            <el-empty description="点击左侧工具栏添加组件">
              <template #image>
                <el-icon :size="100"><Document /></el-icon>
              </template>
            </el-empty>
          </div>
          
          <!-- 组件列表 -->
          <div v-else class="components-list">
            <div 
              v-for="(comp, index) in components" 
              :key="comp.id"
              class="component-item"
              :class="{ active: selectedComponent?.id === comp.id }"
              @click="selectComponent(comp)"
            >
              <div class="component-header">
                <span class="component-title">{{ comp.title }}</span>
                <div class="component-actions">
                  <el-button size="small" @click.stop="editComponent(comp)">✏️</el-button>
                  <el-button size="small" type="danger" @click.stop="removeComponent(comp)">🗑️</el-button>
                </div>
              </div>
              <div class="component-preview">
                <!-- 表格预览 -->
                <el-table v-if="comp.type === 'table'" :data="comp.previewData || []" size="small" max-height="200">
                  <el-table-column 
                    v-for="col in comp.columns" 
                    :key="col.field"
                    :prop="col.field"
                    :label="col.label"
                  />
                </el-table>
                
                <!-- 指标卡预览 -->
                <div v-else-if="comp.type === 'cards'" class="cards-preview">
                  <div v-for="card in comp.cards" :key="card.field" class="preview-card">
                    <div class="card-label">{{ card.label }}</div>
                    <div class="card-value">-</div>
                  </div>
                </div>
                
                <!-- 图表占位 -->
                <div v-else-if="['line', 'bar', 'pie'].includes(comp.type)" class="chart-placeholder">
                  <div class="placeholder-icon">{{ getChartIcon(comp.type) }}</div>
                  <div class="placeholder-text">{{ getChartName(comp.type) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧属性面板 -->
      <div class="right-panel" v-if="selectedComponent">
        <div class="panel-title">⚙️ 组件属性</div>
        <el-form label-width="80px" size="small">
          <el-form-item label="标题">
            <el-input v-model="selectedComponent.title" @change="markChanged" />
          </el-form-item>
          
          <el-form-item label="类型">
            <el-tag>{{ getChartName(selectedComponent.type) }}</el-tag>
          </el-form-item>
          
          <el-form-item label="数据源">
            <el-select v-model="selectedComponent.dataSource" placeholder="选择数据源" size="small" style="width: 100%">
              <el-option label="主数据源" :value="mainQuery" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="列配置">
            <el-button size="small" @click="editColumns">配置列</el-button>
          </el-form-item>
        </el-form>
        
        <div class="panel-section">
          <div class="section-title">数据预览</div>
          <div class="data-preview">
            <pre>{{ JSON.stringify(selectedComponent.previewData || [], null, 2) }}</pre>
          </div>
        </div>
      </div>
    </div>

    <!-- 列配置对话框 -->
    <el-dialog v-model="showColumnDialog" title="配置列" width="600px">
      <el-table :data="availableColumns" border>
        <el-table-column label="显示" width="60">
          <template #default="{ row }">
            <el-checkbox v-model="row.visible" />
          </template>
        </el-table-column>
        <el-table-column prop="field" label="字段" />
        <el-table-column prop="label" label="标题">
          <template #default="{ row }">
            <el-input v-model="row.label" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="格式" width="120">
          <template #default="{ row }">
            <el-select v-model="row.format" size="small" style="width: 100%">
              <el-option label="默认" value="" />
              <el-option label="货币" value="currency" />
              <el-option label="数字" value="number" />
              <el-option label="百分比" value="percent" />
              <el-option label="日期" value="date" />
            </el-select>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showColumnDialog = false">取消</el-button>
        <el-button type="primary" @click="saveColumns">确定</el-button>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog v-model="showPreviewDialog" title="📊 报表预览" width="90%" top="5vh">
      <div class="preview-content">
        <el-empty v-if="components.length === 0" description="请先添加组件" />
        <div v-else class="preview-grid">
          <div v-for="comp in components" :key="comp.id" class="preview-item">
            <h4>{{ comp.title }}</h4>
            <div class="preview-placeholder">
              {{ getChartName(comp.type) }} - 预览功能开发中
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document } from '@element-plus/icons-vue'
import { datasourcesApi, reportsApi } from '@/api'

const router = useRouter()
const route = useRoute()

// 基础数据
const reportName = ref('新报表')
const activeTab = ref('templates')
const selectedDatasource = ref('')
const datasources = ref<any[]>([])
const tableList = ref<any[]>([])
const selectedFields = ref<any[]>([])
const components = ref<any[]>([])
const selectedComponent = ref<any>(null)

// 预设模板
const templates = ref([
  { id: 1, name: '销售统计', icon: '📊', query: 'SELECT * FROM orders' },
  { id: 2, name: '客户分析', icon: '👥', query: 'SELECT * FROM customers' },
  { id: 3, name: '产品排行', icon: '🏆', query: 'SELECT * FROM products' },
  { id: 4, name: '库存监控', icon: '📦', query: 'SELECT * FROM inventory' }
])

// 聚合函数
const aggregateFunctions = ref([
  { label: 'SUM', value: 'SUM', icon: '∑' },
  { label: 'AVG', value: 'AVG', icon: '📊' },
  { label: 'COUNT', value: 'COUNT', icon: '🔢' },
  { label: 'MAX', value: 'MAX', icon: '📈' },
  { label: 'MIN', value: 'MIN', icon: '📉' }
])

// 推荐指标
const recommendedMetrics = ref([
  { name: '总销售额', icon: '💰', desc: 'SUM(amount)', field: 'total_amount' },
  { name: '订单数', icon: '📦', desc: 'COUNT(order_id)', field: 'order_count' },
  { name: '客户数', icon: '👥', desc: 'COUNT(customer_id)', field: 'customer_count' },
  { name: '客单价', icon: '💳', desc: 'AVG(amount)', field: 'avg_order' }
])

// 基础图表
const basicCharts = ref([
  { type: 'table', name: '表格', icon: '📋' },
  { type: 'cards', name: '指标卡', icon: '💳' },
  { type: 'line', name: '折线图', icon: '📈' },
  { type: 'bar', name: '柱状图', icon: '📊' },
  { type: 'pie', name: '饼图', icon: '🥧' }
])

// 高级图表
const advancedCharts = ref([
  { type: 'area', name: '面积图', icon: '🏔️' },
  { type: 'scatter', name: '散点图', icon: '⬤' },
  { type: 'radar', name: '雷达图', icon: '🕸️' },
  { type: 'gauge', name: '仪表盘', icon: '⏱️' }
])

// 对话框
const showColumnDialog = ref(false)
const showPreviewDialog = ref(false)
const availableColumns = ref<any[]>([])

// 加载数据源
const loadDatasources = async () => {
  try {
    const res = await datasourcesApi.list()
    datasources.value = res.data
  } catch (error) {
    ElMessage.error('加载数据源失败')
  }
}

// 加载表结构
const loadTables = async () => {
  if (!selectedDatasource.value) return
  // TODO: 调用 API 加载表结构
  tableList.value = [
    {
      name: 'orders',
      columns: [
        { name: 'order_id', type: 'TEXT' },
        { name: 'customer_name', type: 'TEXT' },
        { name: 'amount', type: 'REAL' },
        { name: 'order_date', type: 'DATE' }
      ]
    }
  ]
}

// 选择表
const handleTableSelect = (node: any) => {
  if (!node.columns) {
    // 是表，加载字段
    selectedFields.value = node.columns.map((col: any) => ({
      name: col.name,
      label: col.name,
      type: col.type,
      visible: true
    }))
    ElMessage.success(`已选择表：${node.name}`)
  }
}

// 应用模板
const applyTemplate = (tpl: any) => {
  ElMessage.success(`应用模板：${tpl.name}`)
  // TODO: 根据模板生成查询和组件
}

// 移除字段
const removeField = (field: any) => {
  selectedFields.value = selectedFields.value.filter(f => f.name !== field.name)
}

// 插入字段
const insertField = (field: any) => {
  ElMessage.success(`添加字段：${field.label}`)
}

// 应用函数
const applyFunction = (fn: any) => {
  ElMessage.success(`应用函数：${fn.label}`)
}

// 插入指标
const insertMetric = (metric: any) => {
  ElMessage.success(`添加指标：${metric.name}`)
}

// 插入图表
const insertChart = (chart: any) => {
  const newComponent = {
    id: 'comp_' + Date.now(),
    type: chart.type,
    title: chart.name,
    dataSource: '',
    columns: [],
    previewData: [],
    config: {}
  }
  components.value.push(newComponent)
  ElMessage.success(`添加组件：${chart.name}`)
}

// 选择组件
const selectComponent = (comp: any) => {
  selectedComponent.value = comp
}

// 编辑组件
const editComponent = (comp: any) => {
  ElMessage.info('编辑功能开发中')
}

// 移除组件
const removeComponent = (comp: any) => {
  ElMessageBox.confirm('确定删除此组件？', '提示', { type: 'warning' })
    .then(() => {
      components.value = components.value.filter(c => c.id !== comp.id)
      if (selectedComponent.value?.id === comp.id) {
        selectedComponent.value = null
      }
      ElMessage.success('删除成功')
    })
    .catch(() => {})
}

// 编辑列
const editColumns = () => {
  if (selectedComponent.value) {
    availableColumns.value = selectedComponent.value.columns || []
    showColumnDialog.value = true
  }
}

// 保存列配置
const saveColumns = () => {
  if (selectedComponent.value) {
    selectedComponent.value.columns = availableColumns.value.filter((c: any) => c.visible)
  }
  showColumnDialog.value = false
  ElMessage.success('保存成功')
}

// 保存报表
const saveReport = async () => {
  if (!reportName.value) {
    ElMessage.warning('请输入报表名称')
    return
  }
  
  try {
    const dsl = {
      dataSource: {},
      components: components.value.map(c => ({
        id: c.id,
        type: c.type,
        title: c.title,
        config: c.config,
        columns: c.columns
      }))
    }
    
    await reportsApi.create({
      name: reportName.value,
      description: '可视化设计器创建',
      dsl_definition: dsl
    })
    
    ElMessage.success('保存成功')
    backToList()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存失败')
  }
}

// 预览报表
const previewReport = () => {
  showPreviewDialog.value = true
}

// 返回
const backToList = () => {
  router.push('/reports')
}

// 获取图表图标
const getChartIcon = (type: string) => {
  const icons: Record<string, string> = {
    line: '📈',
    bar: '📊',
    pie: '🥧',
    table: '📋',
    cards: '💳'
  }
  return icons[type] || '📊'
}

// 获取图表名称
const getChartName = (type: string) => {
  const names: Record<string, string> = {
    line: '折线图',
    bar: '柱状图',
    pie: '饼图',
    table: '表格',
    cards: '指标卡'
  }
  return names[type] || type
}

// 标记已修改
const markChanged = () => {
  // TODO: 显示未保存提示
}

onMounted(() => {
  loadDatasources()
})
</script>

<style scoped>
.report-designer {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.designer-toolbar {
  height: 50px;
  background: white;
  border-bottom: 1px solid #e6e6e6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.toolbar-left, .toolbar-right {
  display: flex;
  gap: 10px;
  align-items: center;
}

.designer-content {
  flex: 1;
  display: grid;
  grid-template-columns: 320px 1fr 280px;
  overflow: hidden;
}

.left-panel {
  background: white;
  border-right: 1px solid #e6e6e6;
  overflow-y: auto;
}

.designer-tabs {
  height: 100%;
  border: none;
}

.designer-tabs :deep(.el-tabs__content) {
  height: calc(100% - 55px);
  overflow-y: auto;
}

.panel-section {
  padding: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 12px;
}

.template-list, .chart-list, .metric-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.template-item, .chart-item, .metric-item {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.template-item:hover, .chart-item:hover, .metric-item:hover {
  background: #ecf5ff;
  border-color: #409EFF;
  transform: translateY(-2px);
}

.template-icon, .chart-icon, .metric-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.template-name, .chart-name {
  font-size: 12px;
  color: #606266;
}

.metric-item {
  display: flex;
  align-items: center;
  gap: 10px;
  text-align: left;
  grid-template-columns: 1fr;
}

.metric-info {
  flex: 1;
}

.metric-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.metric-desc {
  font-size: 11px;
  color: #909399;
  margin-top: 2px;
}

.selected-fields {
  min-height: 100px;
}

.function-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.center-panel {
  background: #f5f7fa;
  overflow: hidden;
}

.edit-canvas {
  height: 100%;
  padding: 20px;
  overflow-y: auto;
}

.empty-canvas {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.components-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.component-item {
  background: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.component-item:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}

.component-item.active {
  border-color: #409EFF;
}

.component-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.component-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.component-actions {
  display: flex;
  gap: 5px;
}

.component-actions .el-button {
  padding: 4px 8px;
  font-size: 12px;
}

.component-preview {
  background: #fafafa;
  border-radius: 4px;
  padding: 10px;
  min-height: 150px;
}

.cards-preview {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.preview-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 15px;
  border-radius: 8px;
  min-width: 100px;
  text-align: center;
}

.card-label {
  font-size: 12px;
  opacity: 0.9;
}

.card-value {
  font-size: 24px;
  font-weight: bold;
  margin-top: 5px;
}

.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 150px;
  color: #909399;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 10px;
}

.placeholder-text {
  font-size: 14px;
}

.right-panel {
  background: white;
  border-left: 1px solid #e6e6e6;
  padding: 20px;
  overflow-y: auto;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #f0f0f0;
}

.data-preview {
  background: #282c34;
  color: #abb2bf;
  padding: 15px;
  border-radius: 4px;
  max-height: 300px;
  overflow: auto;
}

.data-preview pre {
  margin: 0;
  font-size: 12px;
  line-height: 1.5;
}

.preview-content {
  min-height: 400px;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.preview-item {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 20px;
}

.preview-item h4 {
  margin: 0 0 15px 0;
  color: #303133;
}

.preview-placeholder {
  text-align: center;
  padding: 40px;
  color: #909399;
  background: white;
  border-radius: 4px;
}
</style>
