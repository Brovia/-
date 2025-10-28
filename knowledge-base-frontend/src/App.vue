<template>
  <div id="app">
    <el-container class="layout-container">
      <!-- 侧边栏 -->
      <el-aside width="250px" class="sidebar">
        <div class="logo">
          <el-icon><Document /></el-icon>
          <span>知识库管理</span>
        </div>
        
        <el-menu
          :default-active="$route.path"
          class="sidebar-menu"
          router
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409EFF"
        >
          <el-menu-item index="/dashboard">
            <el-icon><House /></el-icon>
            <span>仪表盘</span>
          </el-menu-item>
          
          <el-menu-item index="/upload">
            <el-icon><Upload /></el-icon>
            <span>文档上传</span>
          </el-menu-item>
          
          <el-menu-item index="/search">
            <el-icon><Search /></el-icon>
            <span>知识搜索</span>
          </el-menu-item>
          
          <!-- <el-menu-item index="/qa">
            <el-icon><ChatDotRound /></el-icon>
            <span>智能问答</span>
          </el-menu-item> -->
          
          <el-menu-item index="/documents">
            <el-icon><Folder /></el-icon>
            <span>文档管理</span>
          </el-menu-item>
          
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>系统设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      
      <!-- 主内容区 -->
      <el-container>
        <!-- 顶部导航 -->
        <el-header class="header">
          <div class="header-left">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item 
                v-for="item in breadcrumbs" 
                :key="item.path"
                :to="item.path"
              >
                {{ item.name }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>
          
          <div class="header-right">
            <el-button 
              @click="toggleTheme"
              :icon="theme === 'dark' ? Sunny : Moon"
            >
              {{ theme === 'dark' ? '浅色' : '深色' }}
            </el-button>
          </div>
        </el-header>
        
        <!-- 主要内容 -->
        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { 
  Document, House, Upload, Search, ChatDotRound, 
  Folder, Setting, Sunny, Moon 
} from '@element-plus/icons-vue'

const route = useRoute()

// 主题切换
const theme = ref('light')

// 面包屑导航
const breadcrumbs = computed(() => {
  const pathMap = {
    '/dashboard': { name: '仪表盘', path: '/dashboard' },
    '/upload': { name: '文档上传', path: '/upload' },
    '/search': { name: '知识搜索', path: '/search' },
    // '/qa': { name: '智能问答', path: '/qa' },
    '/documents': { name: '文档管理', path: '/documents' },
    '/settings': { name: '系统设置', path: '/settings' }
  }
  
  return [pathMap[route.path] || { name: '首页', path: '/' }]
})

// 切换主题
const toggleTheme = () => {
  theme.value = theme.value === 'light' ? 'dark' : 'light'
  document.documentElement.setAttribute('data-theme', theme.value)
}

// 初始化
onMounted(() => {
  // 设置默认主题
  document.documentElement.setAttribute('data-theme', theme.value)
})
</script>

<style lang="scss" scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background-color: #304156;
  color: white;
  
  .logo {
    display: flex;
    align-items: center;
    padding: 20px;
    font-size: 18px;
    font-weight: bold;
    border-bottom: 1px solid #434a50;
    
    .el-icon {
      margin-right: 10px;
      font-size: 24px;
    }
  }
  
  .sidebar-menu {
    border: none;
    height: calc(100vh - 80px);
  }
}

.header {
  background-color: #fff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  
  .header-left {
    flex: 1;
  }
  
  .header-right {
    display: flex;
    gap: 10px;
  }
}

.main-content {
  background-color: #f5f5f5;
  padding: 20px;
}

// 深色主题
[data-theme="dark"] {
  .header {
    background-color: #1d1e1f;
    border-bottom-color: #414243;
    color: #e5eaf3;
  }
  
  .main-content {
    background-color: #141414;
    color: #e5eaf3;
  }
}
</style>
