// frontend/src/store/user.js
import { defineStore } from 'pinia'
import { ref } from 'vue'
import request from '../utils/request'
import router from '../router'

export const useUserStore = defineStore('user', () => {
  // 状态定义
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo')) || {})

  // 登录动作
  const login = async (loginForm) => {
    // 封装好的 request 发送请求
    const data = await request.post('/auth/login', loginForm)
    
    token.value = data.access_token
    userInfo.value = data.user
    localStorage.setItem('token', data.access_token)
    localStorage.setItem('userInfo', JSON.stringify(data.user))    
    return data.user
  }

  // 退出动作
  const logout = () => {
    token.value = ''
    userInfo.value = {}
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    router.push('/login')
  }

  return { token, userInfo, login, logout }
})