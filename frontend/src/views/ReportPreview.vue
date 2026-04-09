<template>
  <div class="report-preview" :class="{ 'embed-mode': isEmbed }">
    <!-- 加载中 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>
    
    <!-- 错误状态 -->
    <div v-else-if="error" class="error-container">
      <el-result icon="error" :title="error" sub-title="报表加载失败">
        <template #extra>
          <el-button type="primary" @click="loadReport">重新加载</el-button>
          <el-button @click="goBack">返回列表</el-button>
        </template>
      </el-result>
    </div>
    
    <!-- 报表内容 -->
    <div v-else-if="reportData">
      <!-- 参数配置面板 -->
      <div v-if="parameters.length > 0" class="parameters-panel">
        <el-card class="parameters-card">
          <template #header>
            <div class="card-header">
              <span>📝 报表参数</span>
              <el-button type="primary" size="small" @click="refreshReport">🔄 刷新数据</el-button>
            </div>
          </template>
          
          <el-form :model="paramValues" label-width="120px" size="default">
            <el-form-item 
              v-for="param in parameters" 
              :key="param.name"
              :label="param.label || param.name"
            >
              <!-- 日期类型 -->
              <el-date-picker
                v-if="param.type === 'date'"
                v-model="paramValues[param.name]"
                type="date"
                placeholder="选择日期"
                :default-value="param.default"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
              
              <!-- 数字类型 -->
              <el-input-number
                v-else-if="param.type === 'number'"
                v-model="paramValues[param.name]"
                :default-value="param.default"
                style="width: 100%"
              />
              
              <!-- 字符串类型 -->
              <el-input
                v-else
                v-model="paramValues[param.name]"
                :default-value="param.default"
                :placeholder="`请输入${param.label || param.name}`"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="refreshReport">应用参数</el-button>
              <el-button @click="resetParams">重置参数</el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </div>
      
      <!-- 报表头部 -->
      <header class="report-header">
        <div class="header-top">
          <h1>{{ reportData.name }}</h1>
          <div class="header-actions">
            <el-button @click="goBack">← 返回</el-button>
            <el-button @click="download">📥 下载</el-button>
            <el-button @click="refreshReport">🔄 刷新</el-button>
          </div>
        </div>
        <div class="last-update">最后更新：{{ lastUpdate }}</div>
      </header>
      
      <!-- 报表主体 -->
      <main class="components-grid">
        <div v-for="comp in components" :key="comp.id" class="component-card">
          <h3 class="component-title">{{ comp.title || '未命名组件' }}</h3>
          
          <!-- 表格组件 -->
          <div v-if="comp.type === 'table'" class="table-container">
            <el-table :data="comp.data" style="width: 100%" border stripe size="default">
              <el-table-column 
                v-for="col in comp.columns" 
                :key="col.field"
                :prop="col.field"
                :label="col.label"
                :width="col.width"
              >
                <template #default="{ row }">
                  {{ formatValue(row[col.field], col.format) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
          
          <!-- 指标卡组件 -->
          <div v-else-if="comp.type === 'cards'" class="cards-container">
            <div v-if="comp.config?.chartType" class="cards-chart-wrapper">
              <div :id="'chart-' + comp.id" class="cards-chart-container" style="width: 100%; height: 300px;"></div>
            </div>
            <div v-else class="metrics-grid">
              <div v-for="card in (comp.cards || comp.config?.cards || [])" :key="card.field" class="metric-card">
                <div class="metric-prefix">{{ card.prefix || '' }}</div>
                <div class="metric-value">{{ formatMetric(getCardValue(comp.data, card.field), card.format) }}</div>
                <div class="metric-label">{{ card.label }}</div>
                <div class="metric-suffix">{{ card.suffix || '' }}</div>
              </div>
            </div>
          </div>

          <!-- 图表组件 -->
          <div v-else-if="['line', 'bar', 'pie'].includes(comp.type)" class="chart-wrapper">
            <div :id="'chart-' + comp.id" class="chart-container" style="width: 100%; height: 350px;"></div>
          </div>
        </div>
      </main>
      
      <!-- 报表底部 -->
      <footer class="report-footer">
        <p>Powered by 自定义报表系统</p>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const reportData = ref<any>(null)
const components = ref<any[]>([])
const parameters = ref<any[]>([])
const paramValues = ref<any>({})
const lastUpdate = ref('')
const isEmbed = ref(false)
const charts = ref<any>({})

// 页面加载
onMounted(() => {
  const urlParams = new URLSearchParams(window.location.search)
  isEmbed.value = urlParams.has('embed')
  loadReport()
})

// 加载报表
const loadReport = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const reportId = route.params.reportId as string
    
    // 获取报表详情
    const response = await fetch(`/api/reports/${reportId}`)
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }
    
    const data = await response.json()
    reportData.value = { name: data.name }
    
    // 解析参数
    const dsl = typeof data.dsl_definition === 'string' 
      ? JSON.parse(data.dsl_definition) 
      : data.dsl_definition
    
    parameters.value = dsl.parameters || []
    
    // 初始化参数值
    parameters.value.forEach((p: any) => {
      paramValues.value[p.name] = p.default || ''
    })
    
    // 执行查询获取数据
    await executeQuery()
    
  } catch (e: any) {
    error.value = e.message || '加载失败'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

// 执行查询
const executeQuery = async () => {
  try {
    const reportId = route.params.reportId as string
    
    const response = await fetch(`/api/reports/${reportId}/preview`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ params: paramValues.value })
    })
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }
    
    const result = await response.json()
    components.value = result.components || []
    lastUpdate.value = new Date().toLocaleString('zh-CN')
    
    // 等待 DOM 更新后渲染图表
    await nextTick()
    await nextTick()
    
    setTimeout(() => {
      renderCharts()
    }, 100)
    
  } catch (e: any) {
    ElMessage.error(`数据查询失败：${e.message}`)
  }
}

// 刷新报表
const refreshReport = () => {
  executeQuery()
}

// 重置参数
const resetParams = () => {
  parameters.value.forEach((p: any) => {
    paramValues.value[p.name] = p.default || ''
  })
  ElMessage.info('参数已重置')
}

// 渲染图表
const renderCharts = async () => {
  console.log('🔍 [renderCharts] 开始渲染图表')
  
  await nextTick()
  
  components.value.forEach((comp, index) => {
    console.log(`🔍 [renderCharts] 处理组件 ${index}:`, comp.type)
    
    if (['line', 'bar', 'pie'].includes(comp.type) && comp.data && comp.data.length > 0) {
      renderChart(comp)
    }
    if (comp.type === 'cards' && comp.config?.chartType && comp.data && comp.data.length > 0) {
      renderCardsChart(comp)
    }
  })
  
  console.log('🔍 [renderCharts] 图表渲染完成')
}

const renderChart = (comp: any) => {
  console.log(`🔍 [renderChart] 渲染组件：${comp.id}`)
  
  const chartDom = document.querySelector(`#chart-${comp.id}`) as HTMLElement
  if (!chartDom) {
    console.error(`❌ [renderChart] 找不到图表 DOM：${comp.id}`)
    return
  }
  
  const myChart = echarts.init(chartDom)
  let option: any = {}
  
  // 折线图
  if (comp.type === 'line') {
    const xData = comp.data.map((item: any) => item[comp.config.xField])
    const yFields = comp.config.yFields || [Object.keys(comp.data[0]).find(k => k !== comp.config.xField)]
    
    option = {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: xData },
      yAxis: { type: 'value' },
      series: yFields.map((field: string) => ({
        name: comp.columns?.find((c: any) => c.field === field)?.label || field,
        type: 'line',
        data: comp.data.map((item: any) => item[field]),
        smooth: true
      }))
    }
  }
  // 柱状图
  else if (comp.type === 'bar') {
    const xData = comp.data.map((item: any) => item[comp.config.xField])
    const yField = comp.config.yField || Object.keys(comp.data[0]).find(k => k !== comp.config.xField)
    
    option = {
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'category', data: xData },
      yAxis: { type: 'value' },
      series: [{
        type: 'bar',
        data: comp.data.map((item: any) => item[yField])
      }]
    }
  }
  // 饼图
  else if (comp.type === 'pie') {
    const nameField = comp.config.colorField || comp.columns?.[0]?.field
    const valueField = comp.config.angleField || comp.columns?.[1]?.field
    
    option = {
      tooltip: { trigger: 'item' },
      series: [{
        type: 'pie',
        radius: '50%',
        data: comp.data.map((item: any) => ({
          name: item[nameField],
          value: item[valueField]
        }))
      }]
    }
  }
  
  myChart.setOption(option)
  charts.value[comp.id] = myChart
  
  window.addEventListener('resize', () => myChart.resize())
}

const renderCardsChart = (comp: any) => {
  const chartDom = document.querySelector(`#chart-${comp.id}`) as HTMLElement
  if (!chartDom) return
  
  const myChart = echarts.init(chartDom)
  // TODO: 实现指标卡图表
}

// 格式化值
const formatValue = (value: any, format?: string) => {
  if (value === null || value === undefined) return '-'
  if (format === 'currency') return '¥' + Number(value).toLocaleString()
  if (format === 'number') return Number(value).toLocaleString()
  if (format === 'percent') return (Number(value) * 100).toFixed(2) + '%'
  if (format === 'date') return new Date(value).toLocaleDateString()
  return value
}

const formatMetric = (value: any, format?: string) => {
  return formatValue(value, format)
}

const getCardValue = (data: any[], field: string) => {
  if (!data || !data[0]) return 0
  return data[0][field]
}

// 下载
const download = () => {
  ElMessage.info('下载功能开发中...')
}

// 返回
const goBack = () => {
  router.push('/reports')
}
</script>

<style scoped>
.report-preview {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

.loading-container,
.error-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px;
}

.parameters-panel {
  max-width: 1200px;
  margin: 0 auto 20px;
}

.parameters-card {
  background: white;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.report-header {
  max-width: 1200px;
  margin: 0 auto 20px;
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-top h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.last-update {
  margin-top: 10px;
  color: #909399;
  font-size: 12px;
}

.components-grid {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 20px;
}

.component-card {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.component-title {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 16px;
}

.table-container {
  overflow-x: auto;
}

.cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.metric-card {
  text-align: center;
  padding: 15px 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
  min-width: 120px;
}

.metric-prefix {
  font-size: 20px;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  margin: 8px 0;
}

.metric-label {
  font-size: 12px;
  margin: 5px 0;
}

.chart-wrapper {
  margin-top: 10px;
}

.chart-container {
  border-radius: 8px;
  background: #fafafa;
}

.report-footer {
  max-width: 1200px;
  margin: 20px auto;
  text-align: center;
  color: #909399;
  font-size: 12px;
}

@media (max-width: 768px) {
  .components-grid {
    grid-template-columns: 1fr;
  }
  
  .header-top {
    flex-direction: column;
    gap: 15px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: center;
  }
}
</style>
