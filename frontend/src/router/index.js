// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layout/MainLayout.vue'

const routes = [
  { 
    path: '/', 
    redirect: '/login' 
  },
  { 
    path: '/login', 
    name: 'Login', 
    component: () => import('../views/Login.vue') 
  },
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: 'dashboard',
        name: '控制台首页',
        component: () => import('../views/Dashboard.vue')
      },
      {
        path: 'case-registration',
        name: '收案登记',
        component: () => import('../views/CaseRegistration.vue')
      },
      {
        path: 'case-management',
        name: '案件管理',
        component: () => import('../views/CaseManagement.vue')
      },
      {
        path: 'case-detail/:id',
        name: '案件详情',
        component: () => import('../views/CaseDetail.vue'),
        meta: { hidden: true }
      },
      {
        path: 'lawyer-management',
        name: '律师管理',
        component: () => import('../views/LawyerManagement.vue')
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router