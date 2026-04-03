# 报表预览弹窗功能说明

## ✨ 新增功能

### 📊 可视化预览弹窗

点击报表列表中的 **预览** 按钮，会弹出一个美观的数据预览窗口！

### 功能特点

1. **大数据展示**
   - 弹窗宽度 90%，高度自适应
   - 最大高度 60vh，超出部分滚动
   - 支持数据排序（点击列头）

2. **数据统计**
   - 顶部显示查询结果状态
   - 显示记录总数
   - 渐变紫色背景

3. **数据格式化**
   - 💰 货币格式：`¥1,234.56`
   - 🔢 数字格式：`1,234`
   - 📝 普通文本：原样显示

4. **表格样式**
   - 边框样式
   - 斑马纹（隔行变色）
   - 悬停高亮
   - 默认排序

5. **快捷操作**
   - 📥 导出 Excel
   - 📄 导出 PDF
   - ❌ 关闭弹窗

---

## 🎨 界面效果

### 弹窗头部
```
╔══════════════════════════════════════════════╗
║ 📊 报表预览                              ✕   ║
╠══════════════════════════════════════════════╣
║ ✅ 查询成功      共 4 条记录                 ║
╚══════════════════════════════════════════════╝
```

### 数据表格
```
┌────────────┬──────────┬────────────┬──────────────┐
│ 类别       │ 订单数   │ 销售数量   │ 销售金额     │
├────────────┼──────────┼────────────┼──────────────┤
│ 电子产品   │ 19       │ 101        │ ¥258,099.00  │
│ 家具       │ 10       │ 50         │ ¥60,350.00   │
│ 照明       │ 7        │ 25         │ ¥7,475.00    │
│ 配件       │ 7        │ 23         │ ¥2,047.00    │
└────────────┴──────────┴────────────┴──────────────┘
```

### 底部按钮
```
┌──────────────────────────────────────────────────┐
│  [关闭]     [📥 导出 Excel]  [📄 导出 PDF]      │
└──────────────────────────────────────────────────┘
```

---

## 🔧 技术实现

### 组件结构

```vue
<el-dialog v-model="showPreviewDialog" title="📊 报表预览">
  <div class="preview-container">
    <!-- 统计头部 -->
    <div class="preview-header">
      <el-tag>✅ 查询成功</el-tag>
      <el-tag>共 X 条记录</el-tag>
    </div>
    
    <!-- 数据表格 -->
    <el-table :data="previewData.data">
      <el-table-column 
        v-for="col in previewColumns"
        :prop="col.field"
        :label="col.label"
      >
        <template #default="{ row }">
          <!-- 格式化显示 -->
        </template>
      </el-table-column>
    </el-table>
  </div>
  
  <!-- 底部按钮 -->
  <template #footer>
    <el-button @click="close">关闭</el-button>
    <el-button type="primary" @click="export('excel')">导出 Excel</el-button>
    <el-button type="success" @click="export('pdf')">导出 PDF</el-button>
  </template>
</el-dialog>
```

### 核心代码

```typescript
// 预览处理
const handlePreview = async (row: any) => {
  previewLoading.value = true
  currentReport.value = row
  try {
    const res = await reportsApi.preview(row.id)
    previewData.value = res.data
    previewColumns.value = res.data.components?.[0]?.columns || []
    showPreviewDialog.value = true
    ElMessage.success(`加载 ${res.data.data.length} 条记录`)
  } finally {
    previewLoading.value = false
  }
}

// 货币格式化
const formatCurrency = (value: any) => {
  return Number(value).toLocaleString('zh-CN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}
```

---

## 🎯 使用流程

1. **打开报表列表**
   - 访问 http://0.0.0.0:3000/reports

2. **点击预览按钮**
   - 在任意报表的操作列点击 **预览**

3. **查看数据**
   - 弹窗自动加载数据
   - 支持列排序
   - 支持滚动查看

4. **导出报表**
   - 点击 **导出 Excel** 或 **导出 PDF**
   - 浏览器自动下载文件

5. **关闭弹窗**
   - 点击 **关闭** 按钮
   - 或点击右上角 ✕

---

## 🌟 样式特点

### 渐变色主题
- 弹窗头部：紫色渐变 `#667eea → #764ba2`
- 统计栏：半透明白色背景
- 文字：白色

### 表格样式
- 表头：浅灰背景 `#f5f7fa`
- 斑马纹：隔行浅色
- 悬停：高亮显示
- 边框：细边框

### 响应式
- 弹窗宽度：90%
- 弹窗位置：顶部 5vh
- 内容区域：最大高度 60vh

---

## 📝 格式化规则

| 格式类型 | 示例输入 | 输出显示 |
|---------|---------|----------|
| currency | 258099 | ¥258,099.00 |
| currency | 60350.5 | ¥60,350.50 |
| number | 1234 | 1,234 |
| number | 5678.9 | 5,678.9 |
| default | 电子产品 | 电子产品 |
| default | 2026-04-02 | 2026-04-02 |

---

## 🐛 已知问题

- [ ] 超大数据量（>1000 条）可能渲染较慢
- [ ] 移动端适配待优化

## 🚀 后续优化

- [ ] 添加图表预览（ECharts）
- [ ] 支持数据筛选
- [ ] 支持列宽调整
- [ ] 添加数据导出进度条
- [ ] 支持自定义列显示/隐藏

---

**版本**: v1.1.0  
**更新日期**: 2026-04-02  
**作者**: 自定义报表系统团队
