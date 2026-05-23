<template>
  <div class="layout-shell">
    <aside class="layout-sidebar">
      <div class="layout-sidebar__brand">
        <h1 class="layout-sidebar__title layout-sidebar__title--full">成立律所</h1>
        <h1 class="layout-sidebar__title layout-sidebar__title--short">律所</h1>
      </div>

      <nav class="layout-sidebar__nav">
        <router-link to="/dashboard" class="layout-nav-link" active-class="layout-nav-link--active">
          <el-icon :size="20"><Odometer /></el-icon>
          <span class="layout-nav-link__label">控制台首页</span>
        </router-link>

        <router-link to="/case-registration" class="layout-nav-link" active-class="layout-nav-link--active">
          <el-icon :size="20"><DocumentAdd /></el-icon>
          <span class="layout-nav-link__label">收案登记</span>
        </router-link>

        <router-link to="/case-management" class="layout-nav-link">
          <el-icon :size="20"><Files /></el-icon>
          <span class="layout-nav-link__label">案件管理</span>
        </router-link>

        <router-link
          v-if="['管理员', '风控'].includes(userStore.userInfo.role)"
          to="/lawyer-management"
          class="layout-nav-link"
          active-class="layout-nav-link--active"
        >
          <el-icon :size="20"><Avatar /></el-icon>
          <span class="layout-nav-link__label">律师管理</span>
        </router-link>
      </nav>

      <div class="layout-sidebar__footer">
        <div class="layout-sidebar__user">
          <div class="layout-sidebar__avatar">
            <el-icon><User /></el-icon>
          </div>
          <div class="layout-sidebar__user-meta">
            <p class="text-sm font-bold truncate">{{ userStore.userInfo.full_name || '未知用户' }}</p>
            <p class="text-xs text-blue-200 truncate">{{ userStore.userInfo.role || '无角色' }}</p>
          </div>
        </div>
        <el-button
          @click="handleLogout"
          color="#1e40af"
          class="layout-sidebar__logout !rounded-xl border-none text-white hover:bg-blue-800"
        >
          <span class="layout-sidebar__logout-text">退出登录</span>
          <el-icon class="layout-sidebar__logout-icon"><SwitchButton /></el-icon>
        </el-button>
      </div>
    </aside>

    <main class="layout-main">
      <header class="layout-header">
        <h2 class="text-lg sm:text-xl font-bold text-gray-700 truncate">{{ currentRouteName }}</h2>
        <div class="flex items-center space-x-4 shrink-0">
          <el-badge class="item">
            <el-button circle icon="Bell" class="!border-none !bg-slate-50 hover:!bg-slate-100"></el-button>
          </el-badge>
        </div>
      </header>

      <div class="layout-content">
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
import { Odometer, DocumentAdd, Files, User, Bell, Avatar, SwitchButton } from '@element-plus/icons-vue'
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
.layout-shell {
  display: flex;
  box-sizing: border-box;
  width: 100%;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  gap: 0.75rem;
  padding: 0.75rem;
  background-color: #f8fafc;
}

.layout-sidebar {
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  width: 4.5rem;
  min-width: 4.5rem;
  max-height: 100%;
  overflow: hidden;
  border-radius: 2rem;
  background-color: #2563eb;
  color: #fff;
  box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
  transition: width 0.25s ease, min-width 0.25s ease;
}

.layout-sidebar__brand {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  padding: 1rem 0.5rem;
  border-bottom: 1px solid rgb(255 255 255 / 0.15);
}

.layout-sidebar__title {
  margin: 0;
  font-weight: 700;
  letter-spacing: 0.05em;
  white-space: nowrap;
}

.layout-sidebar__title--full {
  display: none;
  font-size: 1.5rem;
}

.layout-sidebar__title--short {
  font-size: 1rem;
}

.layout-sidebar__nav {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  gap: 0.5rem;
  min-height: 0;
  padding: 0.75rem 0.5rem;
  overflow-x: hidden;
  overflow-y: auto;
}

.layout-nav-link {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 0.875rem 0.75rem;
  border-radius: 1rem;
  color: inherit;
  text-decoration: none;
  transition: background-color 0.2s ease;
}

.layout-nav-link:hover {
  background-color: rgb(255 255 255 / 0.1);
}

.layout-nav-link--active {
  font-weight: 700;
  background-color: rgb(255 255 255 / 0.2);
  box-shadow: inset 0 2px 4px 0 rgb(0 0 0 / 0.05);
}

.layout-nav-link__label {
  display: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.layout-sidebar__footer {
  flex-shrink: 0;
  padding: 0.75rem 0.5rem;
  border-top: 1px solid rgb(255 255 255 / 0.15);
}

.layout-sidebar__user {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  padding: 0.25rem;
}

.layout-sidebar__avatar {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 9999px;
  background-color: rgb(255 255 255 / 0.2);
}

.layout-sidebar__user-meta {
  display: none;
  min-width: 0;
}

.layout-sidebar__logout {
  width: 100%;
  margin-top: 0.75rem;
}

.layout-sidebar__logout-text {
  display: none;
}

.layout-sidebar__logout-icon {
  display: inline-flex;
}

.layout-main {
  display: flex;
  flex: 1 1 auto;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.layout-header {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  height: 5rem;
  margin-bottom: 1rem;
  padding: 0 1.5rem;
  border-radius: 2rem;
  background-color: #fff;
  box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05);
}

.layout-content {
  flex: 1 1 auto;
  min-width: 0;
  min-height: 0;
  overflow-x: auto;
  overflow-y: auto;
  border-radius: 2rem;
}

/* sm: 640px — 与控制台首页 md 断点衔接，侧栏展宽并显示菜单文字 */
@media (min-width: 640px) {
  .layout-shell {
    gap: 1rem;
    padding: 1rem;
  }

  .layout-sidebar {
    width: 12rem;
    min-width: 12rem;
  }

  .layout-sidebar__title--full {
    display: none;
    font-size: 1.25rem;
  }

  .layout-sidebar__title--short {
    display: block;
  }

  .layout-nav-link {
    justify-content: flex-start;
    padding: 1rem;
  }

  .layout-nav-link__label {
    display: inline;
  }

  .layout-sidebar__user {
    justify-content: flex-start;
  }

  .layout-sidebar__user-meta {
    display: block;
  }

  .layout-sidebar__logout-text {
    display: inline;
  }

  .layout-sidebar__logout-icon {
    display: none;
  }
}

/* lg: 1024px — 完整侧栏，与控制台 lg 栅格一致 */
@media (min-width: 1024px) {
  .layout-sidebar {
    width: 16rem;
    min-width: 16rem;
  }

  .layout-sidebar__brand {
    padding: 1.5rem 1rem;
  }

  .layout-sidebar__title--full {
    display: block;
    font-size: 1.5rem;
  }

  .layout-sidebar__title--short {
    display: none;
  }

  .layout-sidebar__nav {
    padding: 1rem;
  }

  .layout-sidebar__footer {
    padding: 1rem;
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
