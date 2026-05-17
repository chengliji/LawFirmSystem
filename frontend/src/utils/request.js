// frontend/src/utils/request.js
import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '../router'

// 创建 axios 实例
const service = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 10000
})

// 请求拦截器：自动在发送请求前加上 JWT Token
service.interceptors.request.use(
  config => {
    // 从 localStorage 获取 token
    const token = localStorage.getItem('token')
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器：统一处理后端报错
service.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    // 处理各种 HTTP 错误状态码
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        ElMessage.error('登录状态已过期，请重新登录')
        localStorage.removeItem('token')
        localStorage.removeItem('userInfo')
        router.push('/login')
      } else if (status === 403) {
        ElMessage.error(data.detail || '您没有权限执行此操作')
      } else {
        ElMessage.error(data.detail || '请求发生错误，请稍后再试')
      }
    } else {
      ElMessage.error('网络连接异常，请检查后端服务')
    }
    return Promise.reject(error)
  }
)

export default service