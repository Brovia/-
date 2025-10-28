<template>
  <div class="dashboard-page">
    <div class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h2>仪表盘</h2>
          <p>知识库系统概览和统计信息</p>
        </div>
        <div class="header-actions">
          <el-button 
            type="primary" 
            :icon="Refresh" 
            :loading="loadingStats"
            @click="refreshStats"
            size="small"
          >
            刷新数据
          </el-button>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <el-alert
      v-if="hasError"
      :title="errorMessage"
      type="error"
      :closable="false"
      show-icon
      class="error-alert"
    />

    <!-- 统计卡片 -->
    <el-row :gutter="24" class="stats-row">
      <el-col :span="8">
        <div class="stat-card stat-card-primary">
          <div class="stat-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-label">文档总数</div>
            <div class="stat-number">{{ stats.total_documents || 0 }}</div>
          </div>
        </div>
      </el-col>
      
      <el-col :span="8">
        <div class="stat-card stat-card-success">
          <div class="stat-icon">
            <el-icon><Collection /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-label">文本块数</div>
            <div class="stat-number">{{ stats.total_chunks || 0 }}</div>
          </div>
        </div>
      </el-col>
      
      <el-col :span="8">
        <div class="stat-card stat-card-warning">
          <div class="stat-icon">
            <el-icon><Cloudy /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-label">云服务商</div>
            <div class="stat-number">{{ stats.providers?.length || 0 }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 云服务商分布 -->
    <el-row :gutter="24">
      <el-col :span="24">
        <div class="providers-card">
          <div class="card-header">
            <h3>云服务商分布</h3>
            <span class="card-subtitle">各云服务商的文档块分布情况</span>
          </div>
          
          <div v-if="stats.providers && stats.providers.length > 0" class="providers-list">
            <div 
              v-for="provider in stats.providers" 
              :key="provider"
              class="provider-item"
            >
              <div class="provider-info">
                <div class="provider-name">
                  <span class="provider-badge" :style="{ backgroundColor: getProviderColor(provider) }"></span>
                  {{ provider }}
                </div>
                <div class="provider-stats">
                  <span class="provider-count">{{ getProviderCount(provider) }}</span> 个文档块
                  <span class="provider-percentage">{{ getProviderPercentage(provider) }}%</span>
                </div>
              </div>
              <el-progress 
                :percentage="getProviderPercentage(provider)"
                :color="getProviderColor(provider)"
                :stroke-width="8"
              />
            </div>
          </div>
          
          <div v-else class="empty-providers">
            <el-empty description="暂无数据" :image-size="100" />
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { onMounted, onActivated, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { 
  Document, Collection, Cloudy, Refresh
} from '@element-plus/icons-vue'
import { useDashboardStore } from '@/stores/dashboard'

const dashboardStore = useDashboardStore()

// 使用store中的状态和方法
const { 
  stats, 
  isLoading: loadingStats, 
  hasError, 
  errorMessage,
  fetchStats,
  refreshStats,
  getProviderPercentage,
  getProviderCount,
  getProviderColor
} = dashboardStore

// 数据加载逻辑
const loadDashboardData = async (forceRefresh = false) => {
  console.log('[Dashboard] 检查缓存状态:', {
    hasData: dashboardStore.hasData,
    isCacheValid: dashboardStore.isCacheValid,
    stats: dashboardStore.stats,
    forceRefresh
  })
  
  // 如果强制刷新或者没有有效缓存，重新加载数据
  if (forceRefresh || !dashboardStore.hasData || !dashboardStore.isCacheValid) {
    try {
      console.log('[Dashboard] 重新加载数据')
      await fetchStats(true) // 强制刷新
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    }
  } else {
    console.log('[Dashboard] 使用缓存数据，无需重新加载')
  }
}

// 组件挂载
onMounted(async () => {
  await loadDashboardData()
  
  // 监听全局数据变化事件
  const handleDataChange = () => {
    console.log('[Dashboard] 收到数据变化通知，强制重新加载数据')
    loadDashboardData(true) // 强制刷新
  }
  
  // 添加全局事件监听器
  window.addEventListener('dashboard-data-changed', handleDataChange)
  
  // 组件卸载时移除监听器
  onUnmounted(() => {
    window.removeEventListener('dashboard-data-changed', handleDataChange)
  })
})

// 组件激活时（从其他页面切换回来时）
onActivated(async () => {
  console.log('[Dashboard] 组件激活，强制重新加载数据')
  // 总是强制重新加载数据，确保数据是最新的
  await loadDashboardData(true)
})

// 监听路由变化，当从其他页面返回时检查是否需要刷新
const route = useRoute()

// 监听路由变化
watch(() => route.path, (newPath, oldPath) => {
  if (newPath === '/dashboard' && oldPath && oldPath !== '/dashboard') {
    console.log('[Dashboard] 路由切换到仪表盘，强制重新加载数据')
    // 总是强制重新加载数据，确保数据是最新的
    loadDashboardData(true)
  }
})
</script>

<style lang="scss" scoped>
.dashboard-page {
  .page-header {
    margin-bottom: 32px;
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }
    
    .header-text {
      flex: 1;
      
      h2 {
        margin-bottom: 8px;
        color: #303133;
        font-size: 28px;
        font-weight: 600;
      }
      
      p {
        color: #909399;
        margin: 0;
        font-size: 14px;
      }
    }
    
    .header-actions {
      margin-left: 20px;
      flex-shrink: 0;
    }
  }
  
  .error-alert {
    margin-bottom: 24px;
  }
  
  .stats-row {
    margin-bottom: 24px;
  }
  
  .stat-card {
    display: flex;
    align-items: center;
    padding: 28px;
    border-radius: 16px;
    background: #fff;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.06);
    transition: all 0.3s ease;
    cursor: pointer;
    position: relative;
    overflow: hidden;
    
    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 4px;
      opacity: 0;
      transition: opacity 0.3s ease;
    }
    
    &:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px 0 rgba(0, 0, 0, 0.12);
      
      &::before {
        opacity: 1;
      }
    }
    
    &.stat-card-primary {
      &::before {
        background: linear-gradient(90deg, #409eff, #66b1ff);
      }
      
      .stat-icon {
        background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
        box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
      }
    }
    
    &.stat-card-success {
      &::before {
        background: linear-gradient(90deg, #67c23a, #85ce61);
      }
      
      .stat-icon {
        background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
        box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
      }
    }
    
    &.stat-card-warning {
      &::before {
        background: linear-gradient(90deg, #e6a23c, #ebb563);
      }
      
      .stat-icon {
        background: linear-gradient(135deg, #e6a23c 0%, #ebb563 100%);
        box-shadow: 0 4px 12px rgba(230, 162, 60, 0.3);
      }
    }
    
    .stat-icon {
      width: 64px;
      height: 64px;
      border-radius: 16px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-right: 20px;
      flex-shrink: 0;
      
      .el-icon {
        font-size: 28px;
        color: white;
      }
    }
    
    .stat-content {
      flex: 1;
      
      .stat-label {
        color: #909399;
        font-size: 14px;
        margin-bottom: 8px;
        font-weight: 500;
      }
      
      .stat-number {
        font-size: 32px;
        font-weight: 700;
        color: #303133;
        line-height: 1;
      }
    }
  }
  
  .providers-card {
    background: #fff;
    border-radius: 16px;
    padding: 28px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.06);
    
    .card-header {
      margin-bottom: 24px;
      padding-bottom: 16px;
      border-bottom: 2px solid #f5f7fa;
      
      h3 {
        margin: 0 0 8px 0;
        color: #303133;
        font-size: 20px;
        font-weight: 600;
      }
      
      .card-subtitle {
        color: #909399;
        font-size: 13px;
      }
    }
  }
  
  .providers-list {
    .provider-item {
      margin-bottom: 24px;
      padding: 16px;
      border-radius: 12px;
      background: #f8f9fa;
      transition: all 0.3s ease;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      &:hover {
        background: #f0f2f5;
        transform: translateX(4px);
      }
      
      .provider-info {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        
        .provider-name {
          font-weight: 600;
          color: #303133;
          font-size: 15px;
          display: flex;
          align-items: center;
          
          .provider-badge {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 10px;
            display: inline-block;
          }
        }
        
        .provider-stats {
          font-size: 13px;
          color: #606266;
          
          .provider-count {
            font-weight: 600;
            color: #303133;
          }
          
          .provider-percentage {
            margin-left: 12px;
            padding: 2px 8px;
            background: #e6f7ff;
            color: #409eff;
            border-radius: 4px;
            font-weight: 600;
            font-size: 12px;
          }
        }
      }
    }
  }
  
  .empty-providers {
    text-align: center;
    padding: 40px 20px;
  }
  
}

[data-theme="dark"] .dashboard-page {
  .page-header {
    h2 {
      color: #e5eaf3;
    }
    
    p {
      color: #a3a6ad;
    }
  }
  
  .stat-card {
    background: #1d1e1f;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.3);
    
    &:hover {
      box-shadow: 0 8px 24px 0 rgba(0, 0, 0, 0.5);
    }
    
    .stat-content {
      .stat-number {
        color: #e5eaf3;
      }
      
      .stat-label {
        color: #a3a6ad;
      }
    }
  }
  
  .providers-card {
    background: #1d1e1f;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.3);
    
    .card-header {
      border-bottom-color: #2d2e2f;
      
      h3 {
        color: #e5eaf3;
      }
      
      .card-subtitle {
        color: #a3a6ad;
      }
    }
  }
  
  .providers-list {
    .provider-item {
      background: #2d2e2f;
      
      &:hover {
        background: #363738;
      }
      
      .provider-info {
        .provider-name {
          color: #e5eaf3;
        }
        
        .provider-stats {
          color: #a3a6ad;
          
          .provider-count {
            color: #e5eaf3;
          }
          
          .provider-percentage {
            background: rgba(64, 158, 255, 0.2);
            color: #66b1ff;
          }
        }
      }
    }
  }
}
</style>
