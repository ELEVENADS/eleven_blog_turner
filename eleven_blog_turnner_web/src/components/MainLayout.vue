<template>
  <t-layout class="main-layout">
    <t-header class="header">
      <div class="header-content">
        <div class="logo" @click="$router.push('/')">
          <div class="logo-icon">
            <t-icon name="article" />
          </div>
          <div class="logo-text">Blog Tuner</div>
        </div>

        <nav class="horizontal-nav">
          <ul class="nav-list">
            <li class="nav-item" :class="{ active: activeMenu === 'dashboard' }" @click="$router.push('/dashboard')">
              <t-icon name="dashboard" />
              <span>仪表盘</span>
            </li>
            <li class="nav-item" :class="{ active: activeMenu === 'notes' }" @click="$router.push('/notes')">
              <t-icon name="pen" />
              <span>笔记管理</span>
            </li>
            <li class="nav-item" :class="{ active: activeMenu === 'styles' }" @click="$router.push('/styles')">
              <t-icon name="sticky-note" />
              <span>风格管理</span>
            </li>
            <li class="nav-item" :class="{ active: activeMenu === 'articles' }" @click="$router.push('/articles')">
              <t-icon name="pen-brush" />
              <span>文章管理</span>
            </li>
            <li class="nav-item" :class="{ active: activeMenu === 'generate' }" @click="$router.push('/generate')">
              <t-icon name="add-circle" />
              <span>生成文章</span>
            </li>
            <li class="nav-item" :class="{ active: activeMenu === 'settings' }" @click="$router.push('/settings')">
              <t-icon name="setting" />
              <span>系统设置</span>
            </li>
          </ul>
        </nav>

        <div class="header-actions">
          <div class="breadcrumb">
            <span v-for="(item, index) in breadcrumbs" :key="index" class="breadcrumb-item">
              {{ item }}
              <span v-if="index < breadcrumbs.length - 1" class="breadcrumb-separator">/</span>
            </span>
          </div>
          <div class="user-menu" @click="toggleUserMenu">
            <t-icon name="user" />
            <span>{{ authStore.user?.username || '用户' }}</span>
            <t-icon name="chevron-down" />
            <div class="user-dropdown" :class="{ show: userMenuOpen }">
              <div class="dropdown-item" @click="handleLogout">退出登录</div>
            </div>
          </div>
        </div>
      </div>
    </t-header>
    <t-content class="content">
      <div class="workspace">
        <div class="file-tree">
          <!-- 文件树区域 -->
          <FileTree v-if="!$slots.fileTree" />
          <slot name="fileTree"></slot>
        </div>
        <div class="content-area">
          <!-- 内容显示区域 -->
          <router-view />
        </div>

        <div class="tool-area">
          <!-- 风格提取和总结工具调用区 -->
          <ToolArea v-if="!$slots.toolArea" />
          <slot name="toolArea"></slot>
        </div>
      </div>
    </t-content>
  </t-layout>
</template>

<script setup lang="ts">
import { computed, ref, watch  } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import FileTree from './FileTree.vue'
import ToolArea from './ToolArea.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const activeMenu = ref('dashboard')

watch(
  () => route.path,
  (path) => {
    const p = path.split('/')[1]
    activeMenu.value = p || 'dashboard'
  },
  { immediate: true }
)
const breadcrumbs = computed(() => {
  const path = route.path.split('/').filter(Boolean)
  return path.map(p => p.charAt(0).toUpperCase() + p.slice(1))
})

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}

// 用户菜单状态
const userMenuOpen = ref(false)

const toggleUserMenu = () => {
  userMenuOpen.value = !userMenuOpen.value
}

// 点击外部关闭用户菜单
document.addEventListener('click', (e) => {
  const userMenu = document.querySelector('.user-menu')
  if (userMenu && !userMenu.contains(e.target as Node)) {
    userMenuOpen.value = false
  }
})


</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.header {
  background: #fff;
  border-bottom: 1px solid #e7e7e7;
  padding: 0 24px;
  display: flex;
  align-items: center;
  height: 64px;
}

.header-content {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 40px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  color: #1890ff;
  transition: all 0.3s;
}

.logo:hover {
  color: #40a9ff;
}

.logo-icon {
  font-size: 24px;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
}

/* 水平导航栏 */
.horizontal-nav {
  flex: 1;
}

.nav-list {
  display: flex;
  list-style: none;
  margin: 0;
  padding: 0;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: #333;
  font-size: 14px;
  position: relative;
  overflow: hidden;
}

.nav-item:hover {
  background-color: #f0f0f0;
  color: #1890ff;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
}

.nav-item.active {
  background-color: #e6f7ff;
  color: #1890ff;
  font-weight: 500;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
}

.nav-item.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 16px;
  right: 16px;
  height: 2px;
  background-color: #1890ff;
  border-radius: 1px;
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.nav-item.active::after {
  transform: scaleX(1);
}

/* 头部操作区 */
.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 24px;
}

/* 面包屑 */
.breadcrumb {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #666;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.breadcrumb-separator {
  color: #999;
}

/* 用户菜单 */
.user-menu {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
  position: relative;
  min-width: 100px;
  justify-content: flex-end;
}

.user-menu:hover {
  background-color: #f0f0f0;
}

.user-dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  background: #fff;
  border: 1px solid #e7e7e7;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  min-width: 120px;
  z-index: 1000;
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
  transform-origin: top right;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
}

.user-dropdown.show {
  opacity: 1;
  transform: translateY(0) scale(1);
  pointer-events: auto;
}

.dropdown-item {
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 14px;
}

.dropdown-item:hover {
  background-color: #f0f0f0;
  color: #1890ff;
}

.content {
  padding: 0;
  background: #f5f5f5;
  overflow: hidden;
  height: calc(100vh - 64px);
}

.workspace {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.file-tree {
  width: 280px;
  background: #fff;
  border-right: 1px solid #e7e7e7;
  overflow: hidden;
  padding: 8px;
}

.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.tool-area {
    width: 300px;
    background: #fff;
    border-left: 1px solid #e7e7e7;
    overflow-y: auto;
    padding: 16px;
  }



@media screen and (max-width: 1200px) {
  .file-tree {
    width: 200px;
  }

  .tool-area {
    width: 250px;
  }
}

@media screen and (max-width: 992px) {
  .tool-area {
    width: 200px;
  }
}

@media screen and (max-width: 768px) {
  .workspace {
    flex-direction: column;
  }

  .file-tree {
    width: 100%;
    height: 200px;
    border-right: none;
    border-bottom: 1px solid #e7e7e7;
  }

  .tool-area {
    width: 100%;
    height: 200px;
    border-left: none;
    border-top: 1px solid #e7e7e7;
  }

  .content-area {
    flex: 1;
  }
}
</style>
