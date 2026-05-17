<template>
  <div class="min-h-screen bg-slate-50 flex">
    <aside class="w-64 bg-blue-600 text-white flex flex-col m-4 rounded-[32px] shadow-xl overflow-hidden transition-all">
      <div class="p-6 flex items-center justify-center border-b border-blue-500/30">
        <h1 class="text-2xl font-bold tracking-wider">成立律所</h1>
      </div>
      
      <nav class="flex-1 p-4 space-y-2 overflow-y-auto">
        <router-link to="/dashboard" class="flex items-center space-x-3 p-4 rounded-2xl hover:bg-white/10 transition-colors" active-class="bg-white/20 font-bold shadow-inner">
          <el-icon :size="20"><Odometer /></el-icon>
          <span>控制台首页</span>
        </router-link>
        
        <router-link to="/case-registration" class="flex items-center space-x-3 p-4 rounded-2xl hover:bg-white/10 transition-colors" active-class="bg-white/20 font-bold shadow-inner">
          <el-icon :size="20"><DocumentAdd /></el-icon>
          <span>收案登记</span>
        </router-link>
        <router-link to="/case-management" class="flex items-center space-x-3 p-4 rounded-2xl hover:bg-white/10 transition-colors">
          <el-icon :size="20"><Files /></el-icon>
          <span>案件管理</span>
        </router-link>
        <router-link v-if="['管理员', '风控'].includes(userStore.userInfo.role)" to="/lawyer-management" class="flex items-center space-x-3 p-4 rounded-2xl hover:bg-white/10 transition-colors" active-class="bg-white/20 font-bold shadow-inner">
          <el-icon :size="20"><Avatar /></el-icon>
          <span>律师管理</span>
        </router-link>
      </nav>

      <div class="p-4 border-t border-blue-500/30">
        <div class="flex items-center space-x-3 p-2">
          <div class="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
            <el-icon><User /></el-icon>
          </div>
          <div>
            <p class="text-sm font-bold">{{ userStore.userInfo.full_name || '未知用户' }}</p>
            <p class="text-xs text-blue-200">{{ userStore.userInfo.role || '无角色' }}</p>
          </div>
        </div>
        <el-button @click="handleLogout" color="#1e40af" class="w-full mt-4 !rounded-xl border-none text-white hover:bg-blue-800" >
          退出登录
        </el-button>
      </div>
    </aside>

    <main class="flex-1 flex flex-col py-4 pr-4 overflow-hidden">
      <header class="bg-white rounded-[32px] h-20 shadow-sm flex items-center justify-between px-8 mb-4">
        <h2 class="text-xl font-bold text-gray-700">{{ currentRouteName }}</h2>
        <div class="flex items-center space-x-4">
          <el-badge  class="item">
            <el-button circle icon="Bell" class="!border-none !bg-slate-50 hover:!bg-slate-100"></el-button>
          </el-badge>
        </div>
      </header>

      <div class="flex-1 overflow-y-auto rounded-[32px]">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Odometer, DocumentAdd, Files, User, Bell, Avatar } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../store/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const currentRouteName = computed(() => {
  return route.name || '概览'
})

// 前端逻辑
const handleUpdatePassword = () => {
  ElMessageBox.prompt('请输入新密码', '修改个人密码', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputType: 'password'
  }).then(async ({ value }) => {
    await request.put('/users/me/password', { new_password: value });
    ElMessage.success('修改成功，下次登录生效');
  });
};

const handleLogout = () => {
  userStore.logout()
  ElMessage.success('已安全退出')
}

</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>