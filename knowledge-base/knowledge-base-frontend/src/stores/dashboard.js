/**
 * 仪表盘数据管理
 * 管理仪表盘统计数据，实现缓存和状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { knowledgeService } from '@/services/api'

export const useDashboardStore = defineStore('dashboard', () => {
  // 从localStorage恢复数据
  const getStoredData = (key, defaultValue = null) => {
    try {
      const stored = localStorage.getItem(`dashboard_${key}`)
      return stored ? JSON.parse(stored) : defaultValue
    } catch (error) {
      console.warn(`Failed to parse stored data for ${key}:`, error)
      return defaultValue
    }
  }

  // 保存数据到localStorage
  const setStoredData = (key, value) => {
    try {
      localStorage.setItem(`dashboard_${key}`, JSON.stringify(value))
    } catch (error) {
      console.warn(`Failed to store data for ${key}:`, error)
    }
  }

  // 状态 - 从localStorage恢复
  const stats = ref(getStoredData('stats', {}))
  const loading = ref(false)
  const error = ref(null)
  const lastFetchTime = ref(getStoredData('lastFetchTime', null))
  const cacheExpiry = ref(getStoredData('cacheExpiry', null))

  // 缓存配置
  const CACHE_DURATION = 5 * 60 * 1000 // 5分钟缓存

  // 计算属性
  const isLoading = computed(() => loading.value)
  const hasError = computed(() => error.value !== null)
  const errorMessage = computed(() => error.value?.message || '')
  const hasData = computed(() => Object.keys(stats.value).length > 0)
  const isCacheValid = computed(() => {
    if (!cacheExpiry.value) return false
    return Date.now() < cacheExpiry.value
  })
  const shouldRefresh = computed(() => {
    if (!lastFetchTime.value) return true
    if (!isCacheValid.value) return true
    return false
  })

  // 获取统计数据
  const fetchStats = async (forceRefresh = false) => {
    // 如果有缓存且不强制刷新，直接返回缓存数据
    if (!forceRefresh && hasData.value && isCacheValid.value) {
      console.log('[Dashboard] 使用缓存数据')
      return stats.value
    }

    try {
      loading.value = true
      error.value = null

      console.log('[Dashboard] 获取统计数据...')
      const response = await knowledgeService.getStats({ showLoading: false })
      
      if (response && response.status === 200) {
        const data = response.data || {}
        const vectorStore = data.vector_store || {}
        
        // 更新统计数据
        stats.value = {
          ...vectorStore,
          total_documents: vectorStore.total_documents || 0,
          total_chunks: vectorStore.total_chunks || 0
        }

        // 更新缓存时间
        lastFetchTime.value = new Date().toISOString()
        cacheExpiry.value = Date.now() + CACHE_DURATION

        // 保存到localStorage
        setStoredData('stats', stats.value)
        setStoredData('lastFetchTime', lastFetchTime.value)
        setStoredData('cacheExpiry', cacheExpiry.value)

        console.log('[Dashboard] 统计数据已更新', stats.value)
        return stats.value
      }
    } catch (err) {
      console.error('[Dashboard] 获取统计数据失败:', err)
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  // 刷新数据
  const refreshStats = async () => {
    return await fetchStats(true)
  }

  // 获取云服务商百分比
  const getProviderPercentage = (provider) => {
    const distribution = stats.value.provider_distribution || {}
    const providerData = distribution[provider]
    return providerData ? providerData.percentage : 0
  }

  // 获取云服务商数量
  const getProviderCount = (provider) => {
    const distribution = stats.value.provider_distribution || {}
    const providerData = distribution[provider]
    return providerData ? providerData.count : 0
  }

  // 获取云服务商颜色
  const getProviderColor = (provider) => {
    const colors = {
      '腾讯云': '#00d4aa',
      '阿里云': '#ff6a00',
      '火山云': '#ff4d4f',
      '华为云': '#ff0000',
      'AWS': '#ff9900',
      'Azure': '#0078d4',
      'GCP': '#4285f4'
    }
    return colors[provider] || '#409eff'
  }

  // 清除缓存
  const clearCache = () => {
    console.log('[Dashboard] 清除缓存数据')
    stats.value = {}
    lastFetchTime.value = null
    cacheExpiry.value = null
    error.value = null
    
    // 清除localStorage中的数据
    localStorage.removeItem('dashboard_stats')
    localStorage.removeItem('dashboard_lastFetchTime')
    localStorage.removeItem('dashboard_cacheExpiry')
    
    console.log('[Dashboard] 缓存已清除，下次访问将重新加载数据')
  }

  // 标记需要刷新（用于跨组件通信）
  const markForRefresh = () => {
    console.log('[Dashboard] 标记需要刷新数据')
    clearCache()
    // 强制设置缓存无效，确保下次访问时重新加载
    cacheExpiry.value = null
    lastFetchTime.value = null
    console.log('[Dashboard] 缓存已标记为无效，下次访问将重新加载')
  }

  // 重置状态
  const reset = () => {
    clearCache()
    loading.value = false
  }

  return {
    // 状态
    stats,
    loading,
    error,
    lastFetchTime,
    cacheExpiry,

    // 计算属性
    isLoading,
    hasError,
    errorMessage,
    hasData,
    isCacheValid,
    shouldRefresh,

    // 方法
    fetchStats,
    refreshStats,
    getProviderPercentage,
    getProviderCount,
    getProviderColor,
    clearCache,
    markForRefresh,
    reset,
  }
})
