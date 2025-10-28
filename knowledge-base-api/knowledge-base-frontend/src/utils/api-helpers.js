/**
 * API工具函数
 * 提供API调用的辅助函数和工具
 */

import { ElMessage } from 'element-plus'

/**
 * 处理API响应
 * @param {Object} response - axios响应对象
 * @param {Object} options - 处理选项
 * @returns {*} 处理后的数据
 */
export const handleApiResponse = (response, options = {}) => {
  const {
    showSuccessMessage = false,
    successMessage = '操作成功',
    extractData = true,
  } = options

  if (showSuccessMessage) {
    ElMessage.success(successMessage)
  }

  return extractData ? response.data : response
}

/**
 * 处理API错误
 * @param {Error} error - 错误对象
 * @param {Object} options - 处理选项
 */
export const handleApiError = (error, options = {}) => {
  const {
    showErrorMessage = true,
    customMessage = null,
    onError = null,
  } = options

  let message = customMessage

  if (!message) {
    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 400:
          message = data?.detail || '请求参数错误'
          break
        case 401:
          message = '认证失败，请检查API密钥'
          break
        case 403:
          message = '权限不足'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 408:
          message = '请求超时'
          break
        case 500:
          message = '服务器内部错误'
          break
        default:
          message = data?.detail || data?.message || '请求失败'
      }
    } else if (error.request) {
      message = '网络连接失败，请检查网络'
    } else {
      message = error.message || '请求配置错误'
    }
  }

  if (showErrorMessage) {
    ElMessage.error(message)
  }

  if (onError) {
    onError(error, message)
  }

  throw error
}

/**
 * 重试机制
 * @param {Function} fn - 要重试的函数
 * @param {number} retries - 重试次数
 * @param {number} delay - 重试延迟(ms)
 * @returns {Promise} 重试结果
 */
export const retryRequest = async (fn, retries = 3, delay = 1000) => {
  try {
    return await fn()
  } catch (error) {
    if (retries > 0) {
      await new Promise(resolve => setTimeout(resolve, delay))
      return retryRequest(fn, retries - 1, delay * 2) // 指数退避
    }
    throw error
  }
}

/**
 * 防抖函数
 * @param {Function} fn - 要防抖的函数
 * @param {number} delay - 延迟时间(ms)
 * @returns {Function} 防抖后的函数
 */
export const debounce = (fn, delay = 300) => {
  let timeoutId
  return (...args) => {
    clearTimeout(timeoutId)
    timeoutId = setTimeout(() => fn.apply(this, args), delay)
  }
}

/**
 * 节流函数
 * @param {Function} fn - 要节流的函数
 * @param {number} delay - 延迟时间(ms)
 * @returns {Function} 节流后的函数
 */
export const throttle = (fn, delay = 300) => {
  let lastCall = 0
  return (...args) => {
    const now = Date.now()
    if (now - lastCall >= delay) {
      lastCall = now
      return fn.apply(this, args)
    }
  }
}

/**
 * 生成缓存键
 * @param {string} prefix - 前缀
 * @param {Object} params - 参数对象
 * @returns {string} 缓存键
 */
export const generateCacheKey = (prefix, params = {}) => {
  const sortedParams = Object.keys(params)
    .sort()
    .map(key => `${key}=${params[key]}`)
    .join('&')
  
  return `${prefix}:${sortedParams}`
}

/**
 * 检查响应是否成功
 * @param {Object} response - API响应
 * @returns {boolean} 是否成功
 */
export const isSuccessResponse = (response) => {
  return response && response.status >= 200 && response.status < 300
}

/**
 * 提取错误信息
 * @param {Error} error - 错误对象
 * @returns {string} 错误信息
 */
export const extractErrorMessage = (error) => {
  if (error.response) {
    return error.response.data?.detail || 
           error.response.data?.message || 
           `HTTP ${error.response.status}`
  }
  if (error.request) {
    return '网络连接失败'
  }
  return error.message || '未知错误'
}

/**
 * 格式化文件大小
 * @param {number} bytes - 字节数
 * @returns {string} 格式化后的大小
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

/**
 * 格式化时间
 * @param {string|Date} date - 日期
 * @returns {string} 格式化后的时间
 */
export const formatTime = (date) => {
  const d = new Date(date)
  const now = new Date()
  const diff = now - d
  
  if (diff < 60000) { // 1分钟内
    return '刚刚'
  } else if (diff < 3600000) { // 1小时内
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) { // 1天内
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return d.toLocaleDateString()
  }
}

/**
 * 验证API密钥格式
 * @param {string} apiKey - API密钥
 * @returns {boolean} 是否有效
 */
export const validateApiKey = (apiKey) => {
  // 简单的API密钥格式验证
  return apiKey && apiKey.length >= 20 && /^[a-zA-Z0-9_-]+$/.test(apiKey)
}

/**
 * 创建FormData对象
 * @param {Object} data - 数据对象
 * @returns {FormData} FormData对象
 */
export const createFormData = (data) => {
  const formData = new FormData()
  
  Object.keys(data).forEach(key => {
    const value = data[key]
    if (value !== null && value !== undefined) {
      if (value instanceof File) {
        formData.append(key, value)
      } else if (Array.isArray(value)) {
        value.forEach((item, index) => {
          formData.append(`${key}[${index}]`, item)
        })
      } else {
        formData.append(key, value)
      }
    }
  })
  
  return formData
}

/**
 * 下载文件
 * @param {Blob} blob - 文件blob
 * @param {string} filename - 文件名
 */
export const downloadFile = (blob, filename) => {
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

// 导出所有工具函数
export default {
  handleApiResponse,
  handleApiError,
  retryRequest,
  debounce,
  throttle,
  generateCacheKey,
  isSuccessResponse,
  extractErrorMessage,
  formatFileSize,
  formatTime,
  validateApiKey,
  createFormData,
  downloadFile,
}
