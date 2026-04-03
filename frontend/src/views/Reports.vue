<template>
  <div class="reports-page">
    <div class="header">
      <h2>报表管理</h2>
      <div class="header-actions">
        <el-button type="success" @click="goToDesigner">🎨 可视化设计</el-button>
        <el-button type="primary" @click="showCreateDialog = true">📝 手动创建</el-button>
      </div>
    </div>

    <el-table :data="reports" v-loading="loading" style="width: 100%">
      <el-table-column prop="name" label="报表名称" />
      <el-table-column prop="description" label="描述" />
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="380">
        <template #default="{ row }">
          <el-button size="small" @click="handlePreview(row)">预览</el-button>
          <el-button size="small" @click="handleExport(row, 'excel')">导出 Excel</el-button>
          <el-button size="small" @click="handleExport(row, 'pdf')">导出 PDF</el-button>
          <el-button size="small" type="success" @click="handleShare(row)">📤 发布</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 预览弹窗 -->
    <el-dialog v-model="showPreviewDialog" title="📊 报表预览" width="90%" top="5vh" :close-on-click-modal="false">
      <div class="preview-container" v-loading="previewLoading">
        <div class="preview-header" v-if="previewData.data">
          <el-tag type="success" size="large">✅ 查询成功</el-tag>
          <el-tag type="info" size="large">共 {{ previewData.data.length }} 条记录</el-tag>
        </div>
        
        <!-- 数据表格 -->
        <el-table 
          v-if="previewData.data && previewData.data.length > 0"
          :data="previewData.data" 
          style="width: 100%"
          border
          stripe
          :default-sort="{prop: Object.keys(previewData.data[0])[0], order: 'ascending'}"
        >
          <el-table-column 
            v-for="(col, index) in previewColumns" 
            :key="index"
            :prop="col.field" 
            :label="col.label"
            :width="col.width || 120"
            sortable
          >
            <template #default="{ row }">
              <span v-if="col.format === 'currency'">
                ¥{{ formatCurrency(row[col.field]) }}
              </span>
              <span v-else-if="col.format === 'number'">
                {{ formatNumber(row[col.field]) }}
              </span>
              <span v-else>
                {{ row[col.field] }}
              </span>
            </template>
          </el-table-column>
        </el-table>
        
        <!-- 空数据提示 -->
        <el-empty v-else description="暂无数据" />
      </div>
      
      <template #footer>
        <el-button @click="showPreviewDialog = false">关闭</el-button>
        <el-button type="primary" @click="exportFromPreview('excel')">📥 导出 Excel</el-button>
        <el-button type="success" @click="exportFromPreview('pdf')">📄 导出 PDF</el-button>
      </template>
    </el-dialog>

    <!-- 新建报表对话框 -->
    <el-dialog v-model="showCreateDialog" title="新建报表" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="报表名称" required>
          <el-input v-model="form.name" placeholder="请输入报表名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" placeholder="请输入描述" />
        </el-form-item>
        <el-form-item label="DSL 定义" required>
          <el-input 
            v-model="form.dsl_definition" 
            type="textarea" 
            :rows="10" 
            placeholder="请输入 JSON 格式的 DSL 定义"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>

    <!-- 分享/发布对话框 -->
    <el-dialog v-model="showShareDialog" title="📤 发布报表" width="700px" :close-on-click-modal="false">
      <div v-if="currentReport" class="share-dialog-content">
        <!-- 创建新分享 -->
        <div class="share-section">
          <h4>✨ 创建新分享链接</h4>
          <el-form :model="shareForm" label-width="120px" size="default">
            <el-form-item label="访问权限">
              <el-select v-model="shareForm.access_level" style="width: 100%">
                <el-option label="🌐 公开访问（任何人可访问）" value="public" />
                <el-option label="🔒 密码保护（需输入密码）" value="password" />
                <el-option label="🏢 仅组织内（需登录）" value="org" />
                <el-option label="🔐 私有（仅创建者）" value="private" />
              </el-select>
            </el-form-item>
            <el-form-item label="访问密码" v-if="shareForm.access_level === 'password'">
              <el-input v-model="shareForm.access_password" placeholder="请输入访问密码" />
            </el-form-item>
            <el-form-item label="过期时间">
              <el-select v-model="shareForm.expires_days" style="width: 100%">
                <el-option label="永久有效" :value="null" />
                <el-option label="7 天后过期" :value="7" />
                <el-option label="30 天后过期" :value="30" />
                <el-option label="90 天后过期" :value="90" />
              </el-select>
            </el-form-item>
            <el-form-item label="最大访问次数">
              <el-input-number v-model="shareForm.max_views" :min="1" :max="10000" style="width: 100%" />
            </el-form-item>
            <el-form-item label="自动刷新">
              <el-select v-model="shareForm.refresh_interval" style="width: 100%">
                <el-option label="不刷新" :value="0" />
                <el-option label="每 30 秒" :value="30" />
                <el-option label="每 1 分钟" :value="60" />
                <el-option label="每 5 分钟" :value="300" />
                <el-option label="每 15 分钟" :value="900" />
              </el-select>
            </el-form-item>
            <el-form-item label="允许下载">
              <el-switch v-model="shareForm.allow_download" />
            </el-form-item>
          </el-form>
          <el-button type="primary" @click="handleCreateShare" style="width: 100%">
            🚀 生成分享链接
          </el-button>
        </div>

        <!-- 已有分享列表 -->
        <div class="share-section" v-if="shareLinks.length > 0">
          <h4>📋 已有分享链接</h4>
          <el-table :data="shareLinks" style="width: 100%" size="small">
            <el-table-column prop="access_level" label="权限" width="80">
              <template #default="{ row }">
                <el-tag size="small" :type="getAccessLevelType(row.access_level)">
                  {{ getAccessLevelLabel(row.access_level) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="分享链接" min-width="200">
              <template #default="{ row }">
                <div class="share-link-cell">
                  <input 
                    class="share-link-input" 
                    :value="getShareUrl(row.share_token)" 
                    readonly 
                    @click="selectLink($event, row.share_token)"
                  />
                  <el-button size="small" @click="copyLink(row.share_token)">复制</el-button>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="过期时间" width="120">
              <template #default="{ row }">
                {{ row.expires_at ? formatDate(row.expires_at) : '永久' }}
              </template>
            </el-table-column>
            <el-table-column label="访问次数" width="80">
              <template #default="{ row }">
                {{ row.view_count || 0 }}{{ row.max_views ? '/' + row.max_views : '' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button size="small" type="danger" @click="handleDeleteShare(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { reportsApi, sharesApi } from '@/api'

const router = useRouter()

const loading = ref(false)
const reports = ref<any[]>([])
const showCreateDialog = ref(false)
const showPreviewDialog = ref(false)
const showShareDialog = ref(false)
const previewLoading = ref(false)
const previewData = ref<any>({ data: [], components: [] })
const previewColumns = ref<any[]>([])
const currentReport = ref<any>(null)
const shareLinks = ref<any[]>([])
const form = ref({
  name: '',
  description: '',
  dsl_definition: ''
})
const shareForm = ref({
  access_level: 'public',
  access_password: '',
  expires_days: null as number | null,
  max_views: 1000,
  refresh_interval: 0,
  allow_download: true,
  allow_refresh: true
})

const loadReports = async () => {
  loading.value = true
  try {
    const res = await reportsApi.list()
    reports.value = res.data
  } catch (error) {
    ElMessage.error('加载报表列表失败')
  } finally {
    loading.value = false
  }
}

const handleCreate = async () => {
  try {
    const dsl = JSON.parse(form.value.dsl_definition)
    await reportsApi.create({
      name: form.value.name,
      description: form.value.description,
      dsl_definition: dsl
    })
    ElMessage.success('创建成功')
    showCreateDialog.value = false
    loadReports()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建失败')
  }
}

const handlePreview = async (row: any) => {
  previewLoading.value = true
  currentReport.value = row
  try {
    const res = await reportsApi.preview(row.id)
    previewData.value = res.data
    previewColumns.value = res.data.components?.[0]?.columns || []
    showPreviewDialog.value = true
    ElMessage.success(`加载 ${res.data.data.length} 条记录`)
  } catch (error) {
    ElMessage.error('预览失败')
  } finally {
    previewLoading.value = false
  }
}

const exportFromPreview = async (format: string) => {
  if (!currentReport.value) return
  await handleExport(currentReport.value, format)
}

const formatCurrency = (value: any) => {
  if (!value && value !== 0) return '0.00'
  return Number(value).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

const formatNumber = (value: any) => {
  if (!value && value !== 0) return '0'
  return Number(value).toLocaleString('zh-CN')
}

const handleExport = async (row: any, format: string) => {
  try {
    const res = await reportsApi.export(row.id, format)
    const blob = new Blob([res.data], { 
      type: format === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    // 修复文件扩展名：excel -> xlsx
    const extension = format === 'pdf' ? 'pdf' : 'xlsx'
    link.download = `${row.name}.${extension}`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除此报表吗？', '提示', { type: 'warning' })
    await reportsApi.delete(row.id)
    ElMessage.success('删除成功')
    loadReports()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const goToDesigner = () => {
  router.push('/designer')
}

// ========== 分享/发布功能 ==========

const handleShare = async (row: any) => {
  currentReport.value = row
  shareLinks.value = []
  showShareDialog.value = true
  // 加载已有的分享链接
  try {
    const res = await sharesApi.listByReport(row.id)
    if (res.data) {
      shareLinks.value = Array.isArray(res.data) ? res.data : [res.data]
    }
  } catch (error) {
    // 忽略错误，可能是还没有分享链接
  }
}

const handleCreateShare = async () => {
  if (!currentReport.value) return
  
  try {
    const payload = { ...shareForm.value }
    // 密码保护时需要密码
    if (payload.access_level === 'password' && !payload.access_password) {
      ElMessage.warning('请设置访问密码')
      return
    }
    
    const res = await sharesApi.create(currentReport.value.id, payload)
    ElMessage.success('分享链接创建成功')
    
    // 刷新分享列表
    const listRes = await sharesApi.listByReport(currentReport.value.id)
    shareLinks.value = Array.isArray(listRes.data) ? listRes.data : [listRes.data]
    
    // 自动复制链接
    copyLink(res.data.share_token)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '创建失败')
  }
}

const handleDeleteShare = async (shareId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除此分享链接吗？', '提示', { type: 'warning' })
    await sharesApi.delete(shareId)
    ElMessage.success('删除成功')
    // 刷新分享列表
    if (currentReport.value) {
      const res = await sharesApi.listByReport(currentReport.value.id)
      shareLinks.value = Array.isArray(res.data) ? res.data : []
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const getShareUrl = (shareToken: string) => {
  const baseUrl = window.location.origin
  return `${baseUrl}/report/${shareToken}`
}

const copyLink = async (shareToken: string) => {
  const url = getShareUrl(shareToken)
  try {
    await navigator.clipboard.writeText(url)
    ElMessage.success('链接已复制到剪贴板')
  } catch (error) {
    // 降级方案
    const input = document.createElement('input')
    input.value = url
    document.body.appendChild(input)
    input.select()
    document.execCommand('copy')
    document.body.removeChild(input)
    ElMessage.success('链接已复制')
  }
}

const selectLink = (event: Event, shareToken: string) => {
  const target = event.target as HTMLInputElement
  target.select()
}

const getAccessLevelLabel = (level: string) => {
  const labels: Record<string, string> = {
    public: '公开',
    password: '密码',
    org: '组织',
    private: '私有'
  }
  return labels[level] || level
}

const getAccessLevelType = (level: string) => {
  const types: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    public: 'success',
    password: 'warning',
    org: 'info',
    private: 'danger'
  }
  return types[level] || 'info'
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '永久'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

// 监听分享对话框打开，重置表单
watch(showShareDialog, (val) => {
  if (val) {
    shareForm.value = {
      access_level: 'public',
      access_password: '',
      expires_days: null,
      max_views: 1000,
      refresh_interval: 0,
      allow_download: true,
      allow_refresh: true
    }
  }
})

onMounted(() => {
  loadReports()
})
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.preview-container {
  max-height: 60vh;
  overflow: auto;
  padding: 10px;
}

.preview-header {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
  padding: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  align-items: center;
}

.preview-header .el-tag {
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  font-weight: 500;
}

:deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 15px 20px;
}

:deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
}

:deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
}

:deep(.el-dialog__headerbtn .el-dialog__close:hover) {
  color: #f0f0f0;
}

:deep(.el-table th) {
  background: #f5f7fa !important;
  color: #606266;
  font-weight: 600;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #fafafa;
}

:deep(.el-table__row:hover) {
  background: #f5f7fa !important;
}

:deep(.el-table td) {
  padding: 12px 0;
}

:deep(.el-dialog__footer) {
  padding: 15px 20px;
  border-top: 1px solid #e6e6e6;
}

/* 分享对话框样式 */
.share-dialog-content {
  max-height: 60vh;
  overflow-y: auto;
  padding: 10px;
}

.share-section {
  margin-bottom: 25px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e6e6e6;
}

.share-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.share-section h4 {
  margin: 0 0 15px 0;
  color: #303133;
  font-size: 15px;
  font-weight: 600;
}

.share-link-cell {
  display: flex;
  gap: 8px;
  align-items: center;
}

.share-link-input {
  flex: 1;
  padding: 6px 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  background: #f5f7fa;
  cursor: pointer;
}

.share-link-input:focus {
  outline: none;
  border-color: #409EFF;
}
</style>
