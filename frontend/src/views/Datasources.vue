<template>
  <div class="datasources-page">
    <div class="header">
      <h2>数据源管理</h2>
      <el-button type="primary" @click="showCreateDialog = true">新建数据源</el-button>
    </div>

    <el-table :data="datasources" v-loading="loading" style="width: 100%">
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="type" label="类型" width="120">
        <template #default="{ row }">
          <el-tag :type="row.type === 'mysql' ? 'success' : 'primary'">
            {{ row.type === 'mysql' ? 'MySQL' : 'PostgreSQL' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="host" label="主机" />
      <el-table-column prop="port" label="端口" width="80" />
      <el-table-column prop="database" label="数据库" />
      <el-table-column label="操作" width="250">
        <template #default="{ row }">
          <el-button size="small" @click="handleTest(row)">测试连接</el-button>
          <el-button size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 新建/编辑数据源对话框 -->
    <el-dialog v-model="showCreateDialog" :title="editMode ? '编辑数据源' : '新建数据源'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="请输入名称" />
        </el-form-item>
        <el-form-item label="类型" required>
          <el-select v-model="form.type" placeholder="请选择类型">
            <el-option label="MySQL" value="mysql" />
            <el-option label="PostgreSQL" value="postgresql" />
            <el-option label="SQLite" value="sqlite" />
          </el-select>
        </el-form-item>
        <el-form-item label="主机" required v-if="form.type !== 'sqlite'">
          <el-input v-model="form.host" placeholder="如：localhost" />
        </el-form-item>
        <el-form-item label="端口" required v-if="form.type !== 'sqlite'">
          <el-input-number v-model="form.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="数据库" required v-if="form.type !== 'sqlite'">
          <el-input v-model="form.database" placeholder="数据库名" />
        </el-form-item>
        <el-form-item label="用户名" required v-if="form.type !== 'sqlite'">
          <el-input v-model="form.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item label="密码" required v-if="form.type !== 'sqlite'">
          <el-input v-model="form.password" type="password" placeholder="密码" />
        </el-form-item>
        
        <!-- SQLite 专属字段 -->
        <el-form-item 
          label="文件路径" 
          required 
          v-if="form.type === 'sqlite'"
        >
          <el-input 
            v-model="form.file_path" 
            placeholder="如：/data/mydb.db 或 :memory:"
          />
          <el-text size="small" style="margin-top: 5px; display: block;">
            💡 提示：使用绝对路径或 :memory: 创建内存数据库
          </el-text>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { datasourcesApi } from '@/api'

const loading = ref(false)
const datasources = ref<any[]>([])
const showCreateDialog = ref(false)
const editMode = ref(false)
const editingId = ref('')
const form = ref({
  name: '',
  type: 'mysql',
  host: 'localhost',
  port: 3306,
  database: '',
  username: '',
  password: '',
  file_path: ''
})

const loadDatasources = async () => {
  loading.value = true
  try {
    const res = await datasourcesApi.list()
    datasources.value = res.data
  } catch (error) {
    ElMessage.error('加载数据源列表失败')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value = {
    name: '',
    type: 'mysql',
    host: 'localhost',
    port: 3306,
    database: '',
    username: '',
    password: '',
    file_path: ''
  }
}

const handleTest = async (row: any) => {
  try {
    await datasourcesApi.test(row.id)
    ElMessage.success('连接成功')
  } catch (error) {
    ElMessage.error('连接失败')
  }
}

const handleEdit = (row: any) => {
  editMode.value = true
  editingId.value = row.id
  form.value = {
    name: row.name,
    type: row.type,
    host: row.host,
    port: row.port,
    database: row.database,
    username: row.username,
    password: '',
    file_path: row.file_path || ''
  }
  showCreateDialog.value = true
}

const handleSubmit = async () => {
  try {
    if (editMode.value) {
      await datasourcesApi.update(editingId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await datasourcesApi.create(form.value)
      ElMessage.success('创建成功')
    }
    showCreateDialog.value = false
    editMode.value = false
    resetForm()
    loadDatasources()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定要删除此数据源吗？', '提示', { type: 'warning' })
    await datasourcesApi.delete(row.id)
    ElMessage.success('删除成功')
    loadDatasources()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadDatasources()
})
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 2px solid #e2e8f0;
}

.header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1a365d;
}
</style>
