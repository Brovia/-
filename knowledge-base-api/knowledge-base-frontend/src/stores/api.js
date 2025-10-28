/**
 * API状态管理
 * 管理API调用状态、缓存和错误处理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'

export const useApiStore = defineStore('api', () => {
  // 状态
  const loading = ref(false)
  const error = ref(null)
  const lastRequestTime = ref(null)
  const requestCount = ref(0)
  const errorCount = ref(0)

  // 缓存
  const cache = ref(new Map())
  const cacheExpiry = ref(new Map())

  // 计算属性
  const isLoading = computed(() => loading.value)
  const hasError = computed(() => error.value !== null)
  const errorMessage = computed(() => error.value?.message || '')
  const isHealthy = computed(() => errorCount.value < 5) // 错误次数少于5次认为健康

  // 请求统计
  const stats = computed(() => ({
    totalRequests: requestCount.value,
    totalErrors: errorCount.value,
    errorRate: requestCount.value > 0 ? (errorCount.value / requestCount.value) * 100 : 0,
    lastRequest: lastRequestTime.value,
    isHealthy: isHealthy.value,
  }))

  // 设置加载状态
  const setLoading = (value) => {
    loading.value = value
  }

  // 设置错误
  const setError = (err) => {
    error.value = err
    errorCount.value++
    
    // 显示错误消息
    if (err?.message) {
      ElMessage.error(err.message)
    }
  }

  // 清除错误
  const clearError = () => {
    error.value = null
  }

  // 记录请求
  const recordRequest = () => {
    requestCount.value++
    lastRequestTime.value = new Date().toISOString()
  }

  // 缓存管理
  const setCache = (key, data, ttl = 300000) => { // 默认5分钟TTL
    cache.value.set(key, data)
    cacheExpiry.value.set(key, Date.now() + ttl)
  }

  const getCache = (key) => {
    const expiry = cacheExpiry.value.get(key)
    if (expiry && Date.now() > expiry) {
      cache.value.delete(key)
      cacheExpiry.value.delete(key)
      return null
    }
    return cache.value.get(key)
  }

  const clearCache = (key) => {
    if (key) {
      cache.value.delete(key)
      cacheExpiry.value.delete(key)
    } else {
      cache.value.clear()
      cacheExpiry.value.clear()
    }
  }

  // 重置状态
  const reset = () => {
    loading.value = false
    error.value = null
    requestCount.value = 0
    errorCount.value = 0
    lastRequestTime.value = null
    clearCache()
  }

  // 健康检查
  const checkHealth = async () => {
    try {
      setLoading(true)
      clearError()
      
      // 这里可以调用实际的健康检查API
      // const response = await apiServices.admin.healthCheck()
      
      return true
    } catch (err) {
      setError(err)
      return false
    } finally {
      setLoading(false)
    }
  }

  return {
    // 状态
    loading,
    error,
    lastRequestTime,
    requestCount,
    errorCount,
    cache,
    cacheExpiry,

    // 计算属性
    isLoading,
    hasError,
    errorMessage,
    isHealthy,
    stats,

    // 方法
    setLoading,
    setError,
    clearError,
    recordRequest,
    setCache,
    getCache,
    clearCache,
    reset,
    checkHealth,
  }
})
