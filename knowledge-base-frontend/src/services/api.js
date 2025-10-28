/**
 * API服务层
 * 统一的API客户端，提供类型安全的API调用
 */

import axios from 'axios'
import { ElMessage, ElLoading } from 'element-plus'
import { APP_CONFIG, API_ENDPOINTS, REQUEST_CONFIG, ERROR_MESSAGES, isDebugEnabled } from '@/config/env.js'

// 获取动态API地址
const getApiBaseUrl = () => {
  try {
    const savedApiSettings = localStorage.getItem('apiSettings')
    if (savedApiSettings) {
      const settings = JSON.parse(savedApiSettings)
      return settings.apiUrl || APP_CONFIG.apiBaseUrl
    }
  } catch (error) {
    console.warn('Failed to parse API settings from localStorage:', error)
  }
  return APP_CONFIG.apiBaseUrl
}

// 创建axios实例
const createApiClient = () => {
  const client = axios.create({
    baseURL: `${getApiBaseUrl()}/api/${APP_CONFIG.apiVersion}`,
    timeout: REQUEST_CONFIG.timeout,
    headers: REQUEST_CONFIG.headers,
  })

  // 错误处理函数（内部函数，可以访问client）
  const handleApiError = async (error) => {
    if (error.response) {
      const { status, data } = error.response
      let message = ERROR_MESSAGES.unknown

      switch (status) {
        case 401:
        case 403:
          message = status === 401 ? ERROR_MESSAGES.unauthorized : ERROR_MESSAGES.forbidden
          ElMessage.error(message)
          return null
        case 404:
          message = ERROR_MESSAGES.notFound
          ElMessage.error(message)
          return null
        case 408:
          message = ERROR_MESSAGES.timeout
          ElMessage.error(message)
          return null
        case 500:
          message = ERROR_MESSAGES.serverError
          ElMessage.error(message)
          return null
        default:
          message = data?.detail || data?.message || ERROR_MESSAGES.unknown
          ElMessage.error(message)
          return null
      }
    } else if (error.request) {
      ElMessage.error(ERROR_MESSAGES.network)
      return null
    } else {
      ElMessage.error(error.message || ERROR_MESSAGES.unknown)
      return null
    }
  }

  // 请求拦截器
  client.interceptors.request.use(
    (config) => {
      // 调试日志
      if (isDebugEnabled) {
        console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, config)
      }

      // 显示加载状态
      if (config.showLoading !== false) {
        config.loadingInstance = ElLoading.service({
          lock: true,
          text: '加载中...',
          background: 'rgba(0, 0, 0, 0.7)'
        })
      }

      return config
    },
    (error) => {
      if (isDebugEnabled) {
        console.error('[API Request Error]', error)
      }
      return Promise.reject(error)
    }
  )

  // 响应拦截器
  client.interceptors.response.use(
    (response) => {
      // 关闭加载状态
      if (response.config.loadingInstance) {
        response.config.loadingInstance.close()
      }

      // 调试日志
      if (isDebugEnabled) {
        console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, response.data)
      }

      return response
    },
    async (error) => {
      // 关闭加载状态
      if (error.config?.loadingInstance) {
        error.config.loadingInstance.close()
      }

      // 调试日志
      if (isDebugEnabled) {
        console.error('[API Response Error]', error)
      }

      // 处理错误响应（可能会返回重试的请求）
      const result = await handleApiError(error)
      if (result) {
        return result
      }
      return Promise.reject(error)
    }
  )

  return client
}

// 创建API客户端实例
let apiClient = createApiClient()

// 重新创建API客户端（用于更新API地址）
const recreateApiClient = () => {
  apiClient = createApiClient()
  return apiClient
}

// 通用请求方法
const request = {
  get: (url, config = {}) => apiClient.get(url, config),
  post: (url, data, config = {}) => apiClient.post(url, data, config),
  put: (url, data, config = {}) => apiClient.put(url, data, config),
  delete: (url, config = {}) => apiClient.delete(url, config),
  patch: (url, data, config = {}) => apiClient.patch(url, data, config),
}

// 知识库API服务
export const knowledgeService = {
  /**
   * 搜索知识库
   * @param {Object} params - 搜索参数
   * @returns {Promise} API响应
   */
  search: (params) => request.get(API_ENDPOINTS.knowledge.search, { params }),

  /**
   * 智能问答
   * @param {Object} data - 问答数据
   * @returns {Promise} API响应
   */
  askQuestion: (data) => request.post(API_ENDPOINTS.knowledge.qa, data),

  /**
   * 文档摘要
   * @param {Object} data - 摘要数据
   * @returns {Promise} API响应
   */
  summarize: (data) => request.post(API_ENDPOINTS.knowledge.summarize, data),

  /**
   * 文档推荐
   * @param {Object} params - 推荐参数
   * @returns {Promise} API响应
   */
  recommend: (params) => request.get(API_ENDPOINTS.knowledge.recommend, { params }),

  /**
   * 获取统计信息
   * @param {Object} config - 请求配置
   * @returns {Promise} API响应
   */
  getStats: (config = {}) => request.get(API_ENDPOINTS.knowledge.stats, config),
}

// 管理API服务
export const adminService = {
  /**
   * 健康检查
   * @param {Object} config - 请求配置
   * @returns {Promise} API响应
   */
  healthCheck: (config = {}) => request.get(API_ENDPOINTS.admin.health, config),

  /**
   * 获取系统指标
   * @returns {Promise} API响应
   */
  getMetrics: () => request.get(API_ENDPOINTS.admin.metrics),

  /**
   * 重建索引
   * @returns {Promise} API响应
   */
  reindex: () => request.post(API_ENDPOINTS.admin.reindex),

  /**
   * 获取文档列表
   * @param {Object} params - 查询参数
   * @param {Object} config - 请求配置
   * @returns {Promise} API响应
   */
  getDocuments: (params = {}, config = {}) => request.get(API_ENDPOINTS.admin.documents, { 
    params, 
    ...config 
  }),

  /**
   * 上传文档
   * @param {FormData} formData - 文件数据
   * @returns {Promise} API响应
   */
  uploadDocument: (formData) => request.post(API_ENDPOINTS.admin.upload, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }),

  /**
   * 删除文档
   * @param {string|number} id - 文档ID
   * @returns {Promise} API响应
   */
  deleteDocument: (id) => request.delete(API_ENDPOINTS.admin.deleteDocument(id)),
}

// 导出所有服务
export const apiServices = {
  knowledge: knowledgeService,
  admin: adminService,
}

// 导出API客户端和请求方法
export { apiClient, request, recreateApiClient }

// 默认导出
export default {
  knowledge: knowledgeService,
  admin: adminService,
  client: apiClient,
  request,
  recreateApiClient,
}
