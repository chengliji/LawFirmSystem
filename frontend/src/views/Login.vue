<template>
  <div class="min-h-screen bg-slate-50 flex items-center justify-center p-4">
    
    <div class="bg-white w-full max-w-5xl rounded-[32px] shadow-2xl shadow-blue-900/10 overflow-hidden flex flex-col md:flex-row h-[600px]">
      
      <div class="md:w-1/2 bg-blue-600 p-12 text-white flex flex-col justify-center relative overflow-hidden hidden md:flex">
        <div class="relative z-10">
          <div class="mb-8 inline-block p-3 bg-white/10 rounded-2xl backdrop-blur-sm">
            <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3"></path></svg>
          </div>
          <h1 class="text-4xl font-bold mb-4 tracking-tight leading-tight">成立律师事务所<br>案件管理系统</h1>
          <p class="text-blue-100 text-lg leading-relaxed mt-4">专业、高效的案件全生命周期管理平台</p>
        </div>
        
        <div class="absolute -bottom-24 -left-24 w-80 h-80 bg-blue-500 rounded-full mix-blend-multiply filter blur-3xl opacity-80"></div>
        <div class="absolute -top-24 -right-24 w-80 h-80 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-50"></div>
      </div>

      <div class="md:w-1/2 p-12 flex flex-col justify-center bg-white">
        <div class="mb-10">
          <h2 class="text-3xl font-bold text-gray-800 mb-3">欢迎登录</h2>
          <p class="text-gray-500">请输入您的专属账号和密码</p>
        </div>

        <el-form :model="loginForm" :rules="rules" ref="loginFormRef" @keyup.enter="handleLogin" size="large">
          <el-form-item prop="username">
            <el-input v-model="loginForm.username" placeholder="请输入用户名" :prefix-icon="User" class="!rounded-xl" />
          </el-form-item>

          <el-form-item prop="password" class="mt-6">
            <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" show-password :prefix-icon="Lock" class="!rounded-xl" />
          </el-form-item>

          <div class="flex items-center justify-between mt-4 mb-8">
            <el-checkbox v-model="rememberMe" class="text-gray-500 font-medium">记住账号</el-checkbox>
            <a href="#" class="text-sm text-blue-600 hover:text-blue-800 font-bold transition-colors">忘记密码？</a>
          </div>

          <el-button type="primary" class="w-full !rounded-2xl !bg-blue-600 !border-blue-600 hover:!bg-blue-700 !h-14 !text-lg font-bold tracking-wider transition-all shadow-lg shadow-blue-600/30" :loading="loading" @click="handleLogin">
            登 录 系 统
          </el-button>
        </el-form>
      </div>
      
    </div>
  </div>
</template>


<script setup>
import { ref, reactive } from 'vue'
import { User, Lock } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../store/user'

const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref(null)
const loading = ref(false)
const rememberMe = ref(true)

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = reactive({
  username: [{ required: true, message: '请输入您的用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入您的密码', trigger: 'blur' }]
})

const handleLogin = async () => {
  if (!loginFormRef.value) return
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const user = await userStore.login(loginForm)
        ElMessage.success(`欢迎回来，${user.full_name}`)
        router.push('/dashboard')
      } catch (error) {
        console.error('登录异常', error)
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
:deep(.el-input__wrapper) {
  border-radius: 1rem; /* 16px 圆角 */
  padding: 12px 20px;
  background-color: #f8fafc; /* slate-50 */
  box-shadow: 0 0 0 1px #e2e8f0 inset; /* slate-200 border */
  transition: all 0.3s;
}
:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px #2563eb inset !important; /* blue-600 focus ring */
  background-color: #ffffff;
}
:deep(.el-input__inner) {
  font-size: 1.05rem;
  color: #1e293b;
}
</style>
