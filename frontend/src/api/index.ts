import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// 报表管理
export const reportsApi = {
  list: () => api.get('/reports'),
  get: (id: string) => api.get(`/reports/${id}`),
  create: (data: any) => api.post('/reports', data),
  update: (id: string, data: any) => api.put(`/reports/${id}`, data),
  delete: (id: string) => api.delete(`/reports/${id}`),
  preview: (id: string, params?: any) => api.get(`/exports/${id}/preview`, { params }),
  export: (id: string, format: string, params?: any) => 
    api.post('/exports/export', { report_id: id, format, params }, { responseType: 'blob' })
}

// 数据源管理
export const datasourcesApi = {
  list: () => api.get('/datasources'),
  get: (id: string) => api.get(`/datasources/${id}`),
  create: (data: any) => api.post('/datasources', data),
  update: (id: string, data: any) => api.put(`/datasources/${id}`, data),
  delete: (id: string) => api.delete(`/datasources/${id}`),
  test: (id: string) => api.post(`/datasources/${id}/test`)
}

// 报表分享/发布
export const sharesApi = {
  // 创建分享链接
  create: (reportId: string, data: any) => api.post(`/reports/${reportId}/share`, data),
  // 获取分享配置
  get: (shareId: string) => api.get(`/shares/${shareId}`),
  // 删除分享链接
  delete: (shareId: string) => api.delete(`/shares/${shareId}`),
  // 获取访问统计
  getStats: (shareId: string) => api.get(`/shares/${shareId}/stats`),
  // 更新分享配置
  update: (shareId: string, data: any) => api.put(`/shares/${shareId}`, data),
  // 获取报表的分享列表
  listByReport: (reportId: string) => api.get(`/reports/${reportId}/shares`)
}
