<template>
  <div class="shared-report" :class="{ 'embed-mode': isEmbed }">
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="10" animated />
    </div>
    
    <div v-else-if="error" class="error-container">
      <el-result icon="error" :title="error" sub-title="报表加载失败">
        <template #extra>
          <el-button type="primary" @click="loadReport">重新加载</el-button>
        </template>
      </el-result>
    </div>
    
    <div v-else-if="reportData">
      <!-- 头部 -->
      <header v-if="config.show_header" class="report-header">
        <div class="header-top">
          <h1>{{ reportData.name }}</h1>
          <div class="header-actions">
            <el-button v-if="config.allow_download" @click="download">📥 下载</el-button>
            <el-button v-if="config.allow_refresh" @click="refresh">🔄 刷新</el-button>
          </div>
        </div>
        <div class="last-update">最后更新：{{ lastUpdate }}</div>
      </header>
      
      <!-- 报表内容 -->
      <main class="components-grid">
        <div v-for="comp in components" :key="comp.id" class="component-card">
          <h3 class="component-title">{{ comp.title }}</h3>
          
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
            <!-- 如果配置了 chartType，则显示 ECharts 图表 -->
            <div v-if="comp.config?.chartType" class="cards-chart-wrapper">
              <div :id="'chart-' + comp.id" class="cards-chart-container" style="width: 100%; height: 300px;"></div>
            </div>
            <!-- 否则显示传统指标卡 -->
            <div v-else>
              <div v-for="card in (comp.cards || comp.config?.cards || [])" :key="card.field" class="metric-card">
                <div class="metric-prefix">{{ card.prefix || '' }}</div>
                <div class="metric-value">{{ formatMetric(getCardValue(comp.data, card.field), card.format) }}</div>
                <div class="metric-label">{{ card.label }}</div>
                <div class="metric-suffix">{{ card.suffix || '' }}</div>
              </div>
            </div>
          </div>

          <!-- 图表容器 -->
          <div v-else-if="['line', 'bar', 'pie'].includes(comp.type)" class="chart-wrapper">
            <div :id="'chart-' + comp.id" class="chart-container" style="width: 100%; height: 350px;"></div>
          </div>
        </div>
      </main>
      
      <!-- 底部 -->
      <footer v-if="config.show_footer" class="report-footer">
        <p>Powered by 自定义报表系统</p>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const route = useRoute()
const loading = ref(true)
const error = ref('')
const reportData = ref<any>(null)
const components = ref<any[]>([])
const config = ref({
  allow_download: true,
  allow_refresh: true,
  refresh_interval: 0,
  show_header: true,
  show_footer: true
})
const lastUpdate = ref('')
const isEmbed = ref(false)
const charts = ref<any>({})

// 检查是否嵌入模式
onMounted(() => {
  const urlParams = new URLSearchParams(window.location.search)
  isEmbed.value = urlParams.has('embed')
  loadReport()
})

// 渲染图表
const renderCharts = async () => {
  console.log('🔍 [renderCharts] 开始渲染图表')
  console.log('🔍 [renderCharts] components:', components.value)
  console.log('🔍 [renderCharts] echarts 实例:', echarts)
  
  await nextTick()
  
  components.value.forEach((comp, index) => {
    console.log(`🔍 [renderCharts] 处理组件 ${index}:`, comp)
    console.log(`🔍 [renderCharts] 组件类型:`, comp.type)
    console.log(`🔍 [renderCharts] 组件数据:`, comp.data)
    
    if (['line', 'bar', 'pie'].includes(comp.type) && comp.data && comp.data.length > 0) {
      console.log(`🔍 [renderCharts] 准备渲染图表：${comp.id}, 类型：${comp.type}`)
      renderChart(comp)
    }
    // 指标卡带图表的情况
    if (comp.type === 'cards' && comp.config?.chartType && comp.data && comp.data.length > 0) {
      console.log(`🔍 [renderCharts] 准备渲染指标卡图表：${comp.id}`)
      renderCardsChart(comp)
    }
  })
  
  console.log('🔍 [renderCharts] 图表渲染完成')
}

const renderChart = (comp: any) => {
  console.log(`🔍 [renderChart] 开始渲染组件：${comp.id}`)
  console.log(`🔍 [renderChart] 组件配置:`, comp.config)
  
  // 使用 querySelector 代替 getElementById，更可靠
  const chartDom = document.querySelector(`#chart-${comp.id}`) as HTMLElement
  console.log(`🔍 [renderChart] chart DOM 元素:`, chartDom)
  
  if (!chartDom) {
    console.error(`❌ [renderChart] 找不到图表 DOM 元素：chart-${comp.id}`)
    return
  }
  
  console.log(`🔍 [renderChart] 初始化 ECharts 实例`)
  const myChart = echarts.init(chartDom)
  console.log(`🔍 [renderChart] ECharts 实例已创建:`, myChart)
  
  let option: any = {}
  
  if (comp.type === 'line') {
    const xData = comp.data.map((item: any) => item[comp.config.xField])
    const yFields = comp.config.yFields || [Object.keys(comp.data[0]).find(k => k !== comp.config.xField)]
    
    option = {
      tooltip: {
        trigger: 'axis',
        formatter: (params: any) => {
          let result = params[0].name + '<br/>'
          params.forEach((p: any) => {
            result += p.marker + p.seriesName + ': ¥' + Number(p.value).toLocaleString() + '<br/>'
          })
          return result
        }
      },
      legend: {
        data: yFields.map((f: string) => comp.columns?.find((c: any) => c.field === f)?.label || f)
      },
      xAxis: {
        type: 'category',
        data: xData,
        axisLabel: { rotate: 45 }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (value: number) => '¥' + value.toLocaleString()
        }
      },
      series: yFields.map((field: string, idx: number) => ({
        name: comp.columns?.find((c: any) => c.field === field)?.label || field,
        type: 'line',
        data: comp.data.map((item: any) => item[field]),
        smooth: comp.config.smooth !== false,
        areaStyle: comp.config.areaStyle || { opacity: 0 },
        itemStyle: { pointSize: 5, pointShape: 'circle' },
        lineStyle: { width: comp.config.lineStyle?.width || 2 }
      }))
    }
  } else if (comp.type === 'bar') {
    const xData = comp.data.map((item: any) => item[comp.config.xField])
    const yField = comp.config.yField || Object.keys(comp.data[0]).find(k => k !== comp.config.xField)
    const seriesField = comp.config.seriesField
    
    if (seriesField) {
      const groups = [...new Set(comp.data.map((item: any) => item[seriesField]))]
      option = {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        legend: { data: groups },
        xAxis: { type: 'category', data: xData, axisLabel: { rotate: 45 } },
        yAxis: { type: 'value', axisLabel: { formatter: (value: number) => '¥' + value.toLocaleString() } },
        series: groups.map((group: string) => ({
          name: group,
          type: 'bar',
          data: comp.data.filter((item: any) => item[seriesField] === group).map((item: any) => item[yField]),
          barWidth: '60%'
        }))
      }
    } else {
      option = {
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        xAxis: { type: 'category', data: xData, axisLabel: { rotate: 45 } },
        yAxis: { type: 'value', axisLabel: { formatter: (value: number) => '¥' + value.toLocaleString() } },
        series: [{
          name: comp.columns?.find((c: any) => c.field === yField)?.label || yField,
          type: 'bar',
          data: comp.data.map((item: any) => item[yField]),
          barWidth: '60%',
          label: { show: true, position: 'top', formatter: (params: any) => '¥' + params.value.toLocaleString() }
        }]
      }
    }
  } else if (comp.type === 'pie') {
    const nameField = comp.config.colorField || comp.columns?.[0]?.field || Object.keys(comp.data[0])[0]
    const valueField = comp.config.angleField || comp.columns?.find((c: any) => c.format !== 'percent')?.field || Object.keys(comp.data[0]).find(k => k !== nameField)
    
    option = {
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { orient: 'vertical', left: 'left' },
      series: [{
        name: comp.title,
        type: 'pie',
        radius: comp.config.innerRadius ? [comp.config.innerRadius * 100 + '%', comp.config.radius * 100 + '%'] : (comp.config.radius * 100 + '%'),
        data: comp.data.map((item: any) => ({ name: item[nameField], value: item[valueField] })),
        emphasis: {
          itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' }
        },
        label: { formatter: '{b}: {d}%' }
      }]
    }
  }
  
  console.log(`🔍 [renderChart] 设置图表配置 option:`, option)
  console.log(`🔍 [renderChart] 调用 setOption`)
  
  try {
    myChart.setOption(option)
    console.log(`✅ [renderChart] 图表设置成功：${comp.id}`)
    charts.value[comp.id] = myChart
    console.log(`🔍 [renderChart] 图表实例已保存`)
  } catch (error) {
    console.error(`❌ [renderChart] 设置图表失败：${comp.id}`, error)
  }
  
  window.addEventListener('resize', () => {
    myChart.resize()
  })
  console.log(`🔍 [renderChart] 图表渲染完成：${comp.id}`)
}

const renderCardsChart = (comp: any) => {
  console.log(`🔍 [renderCardsChart] 开始渲染指标卡图表：${comp.id}`)
  
  // 使用 querySelector 代替 getElementById，更可靠
  const chartDom = document.querySelector(`#chart-${comp.id}`) as HTMLElement
  console.log(`🔍 [renderCardsChart] chart DOM 元素:`, chartDom)
  
  if (!chartDom) {
    console.error(`❌ [renderCardsChart] 找不到图表 DOM 元素：chart-${comp.id}`)
    return
  }

  console.log(`🔍 [renderCardsChart] 初始化 ECharts 实例`)
  const myChart = echarts.init(chartDom)
  console.log(`🔍 [renderCardsChart] ECharts 实例已创建`)
  
  const chartType = comp.config.chartType
  const cards = comp.cards || comp.config?.cards || []
  const data = comp.data[0] || {}

  // 准备数据
  const names = cards.map((c: any) => c.label || c.field)
  const values = cards.map((c: any) => {
    const val = data[c.field]
    return val !== null && val !== undefined ? Number(val) : 0
  })

  let option: any = {}

  if (chartType === 'gauge') {
    // 仪表盘风格 - 适合单个或少数指标
    option = {
      series: cards.map((card: any, idx: number) => {
        const total = cards.length
        const angle = 360 / total
        const startAngle = -90 + idx * angle
        return {
          type: 'gauge',
          startAngle: startAngle,
          endAngle: startAngle + angle - 5,
          min: card.min || 0,
          max: card.max || Math.max(values[idx] * 1.5, 100),
          radius: '90%',
          center: ['50%', '50%'],
          progress: {
            show: true,
            width: 12,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: '#667eea' },
                { offset: 1, color: '#764ba2' }
              ])
            }
          },
          pointer: { show: false },
          axisLine: { lineStyle: { width: 12, color: [[1, '#eee']] } },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          detail: {
            valueAnimation: true,
            formatter: (val: number) => {
              if (card.format === 'currency') return '¥' + val.toLocaleString()
              if (card.format === 'percent') return val.toFixed(1) + '%'
              return val.toLocaleString()
            },
            fontSize: 20,
            fontWeight: 'bold',
            color: '#333',
            offsetCenter: [0, '30%']
          },
          title: {
            offsetCenter: [0, '60%'],
            fontSize: 12,
            color: '#666'
          },
          data: [{
            value: values[idx],
            name: card.prefix ? card.prefix + ' ' + (card.label || card.field) : (card.label || card.field)
          }]
        }
      })
    }
  } else if (chartType === 'bar') {
    // 柱状图风格 - 适合对比多个指标
    option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: (params: any) => {
          const p = params[0]
          const card = cards[p.dataIndex]
          let val = p.value
          if (card?.format === 'currency') val = '¥' + val.toLocaleString()
          else if (card?.format === 'percent') val = val.toFixed(2) + '%'
          else val = val.toLocaleString()
          return `${p.name}<br/>${val}`
        }
      },
      grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
      xAxis: {
        type: 'category',
        data: names,
        axisLabel: { fontSize: 11, rotate: 15 },
        axisTick: { alignWithLabel: true }
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          formatter: (val: number) => {
            if (values.some(v => v > 10000)) return (val / 10000).toFixed(0) + '万'
            return val.toLocaleString()
          }
        }
      },
      series: [{
        name: comp.title,
        type: 'bar',
        data: values,
        barWidth: '50%',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#667eea' },
            { offset: 1, color: '#764ba2' }
          ]),
          borderRadius: [4, 4, 0, 0]
        },
        label: {
          show: true,
          position: 'top',
          formatter: (params: any) => {
            const card = cards[params.dataIndex]
            const val = params.value
            if (card?.format === 'currency') return '¥' + val.toLocaleString()
            if (card?.format === 'percent') return val.toFixed(2) + '%'
            return val.toLocaleString()
          },
          fontSize: 11
        }
      }]
    }
  } else if (chartType === 'radar') {
    // 雷达图 - 适合多维度对比
    const maxValue = Math.max(...values) * 1.2
    option = {
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          const card = cards[params.dataIndex]
          let val = params.value
          if (card?.format === 'currency') val = '¥' + val.toLocaleString()
          else if (card?.format === 'percent') val = val.toFixed(2) + '%'
          else val = val.toLocaleString()
          return `${params.name}<br/>${val}`
        }
      },
      radar: {
        indicator: names.map(name => ({ name, max: maxValue })),
        radius: '70%',
        axisName: { fontSize: 11 },
        splitArea: { areaStyle: { color: ['#f8f9fa', '#fff'] } }
      },
      series: [{
        type: 'radar',
        data: [{
          value: values,
          name: comp.title,
          areaStyle: { color: 'rgba(102, 126, 234, 0.3)' },
          lineStyle: { color: '#667eea', width: 2 },
          itemStyle: { color: '#667eea' },
          label: {
            show: true,
            formatter: (params: any) => {
              const card = cards[params.dataIndex]
              const val = params.value
              if (card?.format === 'currency') return '¥' + val.toLocaleString()
              if (card?.format === 'percent') return val.toFixed(1) + '%'
              return val.toLocaleString()
            },
            fontSize: 10
          }
        }]
      }]
    }
  } else if (chartType === 'funnel') {
    // 漏斗图 - 适合流程转化
    const sortedData = cards.map((c: any, i: number) => ({
      name: c.label || c.field,
      value: values[i]
    })).sort((a: any, b: any) => b.value - a.value)

    option = {
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          const card = cards.find((c: any) => (c.label || c.field) === params.name)
          let val = params.value
          if (card?.format === 'currency') val = '¥' + val.toLocaleString()
          else if (card?.format === 'percent') val = val.toFixed(2) + '%'
          else val = val.toLocaleString()
          return `${params.name}<br/>${val}`
        }
      },
      legend: { orient: 'vertical', left: 'left', textStyle: { fontSize: 11 } },
      series: [{
        type: 'funnel',
        left: '20%',
        width: '60%',
        min: 0,
        max: Math.max(...values),
        minSize: '0%',
        maxSize: '100%',
        sort: 'descending',
        gap: 5,
        label: {
          show: true,
          position: 'inside',
          formatter: (params: any) => {
            const card = cards.find((c: any) => (c.label || c.field) === params.name)
            if (card?.format === 'currency') return '¥' + params.value.toLocaleString()
            if (card?.format === 'percent') return params.value.toFixed(2) + '%'
            return params.value.toLocaleString()
          },
          fontSize: 11
        },
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 1
        },
        data: sortedData
      }]
    }
  }

  console.log(`🔍 [renderCardsChart] 设置图表配置 option`)
  
  try {
    myChart.setOption(option)
    console.log(`✅ [renderCardsChart] 图表设置成功：${comp.id}`)
    charts.value[comp.id] = myChart
  } catch (error) {
    console.error(`❌ [renderCardsChart] 设置图表失败：${comp.id}`, error)
  }

  window.addEventListener('resize', () => {
    myChart.resize()
  })
  console.log(`🔍 [renderCardsChart] 图表渲染完成：${comp.id}`)
}

const loadReport = async () => {
  loading.value = true
  error.value = ''
  
  try {
    const shareToken = route.params.shareToken as string
    // 调用后端 API 获取报表数据（JSON）
    const response = await fetch(`/api/shares/${shareToken}/data`)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }
    
    const data = await response.json()
    
    reportData.value = { name: data.name }
    config.value = data.config
    components.value = data.components
    lastUpdate.value = new Date().toLocaleString('zh-CN')
    
    console.log('Report loaded:', data)
    
    // 等待 DOM 完全渲染后再渲染图表
    await nextTick()
    await nextTick()
    console.log('🔍 [loadReport] DOM 已更新，开始渲染图表')
    
    // 使用 setTimeout 确保 DOM 完全准备好
    setTimeout(async () => {
      console.log('🔍 [loadReport] setTimeout 触发，开始渲染图表')
      await renderCharts()
    }, 100)
    
    // 自动刷新
    if (config.value.refresh_interval > 0) {
      setInterval(refresh, config.value.refresh_interval * 1000)
    }
  } catch (e: any) {
    error.value = e.message || '加载失败'
    ElMessage.error(error.value)
  } finally {
    loading.value = false
  }
}

const refresh = () => {
  lastUpdate.value = new Date().toLocaleString('zh-CN')
  ElMessage.success('数据已刷新')
}

const download = () => {
  ElMessage.info('下载功能开发中...')
}

const formatValue = (value: any, format?: string) => {
  if (value === null || value === undefined) return '-'
  if (format === 'currency') {
    return '¥' + Number(value).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
  } else if (format === 'number') {
    return Number(value).toLocaleString('zh-CN')
  } else if (format === 'percent') {
    return (Number(value) * 100).toFixed(2) + '%'
  } else if (format === 'date') {
    return new Date(value).toLocaleDateString('zh-CN')
  }
  return value
}

const formatMetric = (value: any, format?: string) => {
  if (value === null || value === undefined) return '0'
  if (format === 'currency') {
    return '¥' + Number(value).toLocaleString('zh-CN', { minimumFractionDigits: 2 })
  } else if (format === 'number') {
    return Number(value).toLocaleString('zh-CN')
  }
  return value
}

const getCardValue = (data: any[], field: string) => {
  if (!data || !data[0]) return 0
  return data[0][field]
}
</script>

<style scoped>
.shared-report {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

.shared-report.embed-mode {
  background: transparent;
  padding: 0;
}

.shared-report.embed-mode header,
.shared-report.embed-mode footer {
  display: none;
}

.loading-container, .error-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
}

.report-header {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.1);
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.header-top h1 {
  margin: 0;
  color: #303133;
  font-size: 24px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.last-update {
  color: #909399;
  font-size: 14px;
}

.components-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
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
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.cards-chart-wrapper {
  margin-top: 10px;
}

.cards-chart-container {
  border-radius: 8px;
  background: #fafafa;
}

.metric-card {
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
  min-width: 150px;
}

.metric-prefix {
  font-size: 24px;
  margin-bottom: 10px;
}

.metric-value {
  font-size: 32px;
  font-weight: bold;
  margin: 10px 0;
}

.metric-label {
  font-size: 14px;
  opacity: 0.9;
}

.metric-suffix {
  font-size: 14px;
  opacity: 0.8;
  margin-top: 5px;
}

.chart-placeholder {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 30px;
  text-align: center;
}

.chart-hint {
  color: #606266;
  font-size: 16px;
  margin-bottom: 10px;
}

.chart-note {
  color: #909399;
  font-size: 14px;
  margin-bottom: 20px;
}

.chart-data-preview {
  text-align: left;
  background: white;
  border-radius: 4px;
  padding: 15px;
}

.chart-data-preview pre {
  max-height: 200px;
  overflow: auto;
  font-size: 12px;
  background: #282c34;
  color: #abb2bf;
  padding: 15px;
  border-radius: 4px;
}

.report-footer {
  text-align: center;
  padding: 20px;
  color: #909399;
  font-size: 14px;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .components-grid {
    grid-template-columns: 1fr;
  }
  
  .metric-card {
    min-width: 100%;
  }
}
</style>
