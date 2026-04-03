import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/reports'
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/views/Reports.vue')
  },
  {
    path: '/datasources',
    name: 'Datasources',
    component: () => import('@/views/Datasources.vue')
  },
  {
    path: '/report/:shareToken',
    name: 'SharedReport',
    component: () => import('@/views/SharedReport.vue')
  },
  {
    path: '/designer',
    name: 'ReportDesigner',
    component: () => import('@/views/ReportDesigner.vue')
  },
  {
    path: '/designer/:id',
    name: 'ReportDesignerEdit',
    component: () => import('@/views/ReportDesigner.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
