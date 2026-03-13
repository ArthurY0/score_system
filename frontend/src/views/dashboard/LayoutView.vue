<template>
  <el-container class="layout">
    <el-aside width="220px">
      <div class="sidebar-logo">成绩管理系统</div>
      <el-menu :default-active="activeMenu" router>
        <el-menu-item index="/">
          <el-icon><Odometer /></el-icon>
          <span>工作台</span>
        </el-menu-item>
        <el-sub-menu index="statistics">
          <template #title>
            <el-icon><DataAnalysis /></el-icon>
            <span>统计分析</span>
          </template>
          <el-menu-item index="/statistics/class">班级统计</el-menu-item>
          <el-menu-item index="/statistics/grade">年级统计</el-menu-item>
          <el-menu-item index="/statistics/student">学生统计</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/reports">
          <el-icon><Download /></el-icon>
          <span>报表导出</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header>
        <div class="header-right">
          <span>{{ authStore.user?.name }}</span>
          <el-button text @click="handleLogout">退出</el-button>
        </div>
      </el-header>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const activeMenu = computed(() => route.path)

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout { height: 100vh; }
.sidebar-logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  font-size: 16px;
  font-weight: bold;
  background: #001529;
  color: #fff;
}
.el-header {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  border-bottom: 1px solid #eee;
}
.header-right { display: flex; align-items: center; gap: 12px; }
</style>
