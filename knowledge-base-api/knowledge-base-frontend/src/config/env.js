/**
 * 环境配置管理
 * 统一管理应用的环境变量和配置
 */

// 获取环境变量，提供默认值
const getEnvVar = (key, defaultValue = '') => {
  return import.meta.env[key] || defaultValue
}

// 应用配置
export const APP_CONFIG = {
  // 应用信息
  title: getEnvVar('VITE_APP_TITLE', '知识库管理系统'),
  version: getEnvVar('VITE_APP_VERSION', '1.0.0'),
  environment: getEnvVar('VITE_APP_ENV', 'development'),
  
  // API配置
  apiBaseUrl: getEnvVar('VITE_API_BASE_URL', 'http://localhost:8000'),
  apiTimeout: parseInt(getEnvVar('VITE_API_TIMEOUT', '30000')),
  apiVersion: getEnvVar('VITE_API_VERSION', 'v1'),
  
  // 功能开关
  enableDebug: getEnvVar('VITE_ENABLE_DEBUG', 'true') === 'true',
  enableMock: getEnvVar('VITE_ENABLE_MOCK', 'false') === 'true',
  
  // 第三方服务
  analyticsId: getEnvVar('VITE_ANALYTICS_ID', ''),
  sentryDsn: getEnvVar('VITE_SENTRY_DSN', ''),
}

// API端点配置
export const API_ENDPOINTS = {
  // 知识库API
  knowledge: {
    search: '/knowledge/search',
    qa: '/knowledge/qa',
    summarize: '/knowledge/summarize',
    recommend: '/knowledge/recommend',
    stats: '/knowledge/stats',
  },
  
  // 管理API
  admin: {
    health: '/admin/health',
    metrics: '/admin/metrics',
    reindex: '/admin/reindex',
    documents: '/admin/documents',
    upload: '/admin/documents/upload',
    deleteDocument: (id) => `/admin/documents/${id}`,
  },
}

// 请求配置
export const REQUEST_CONFIG = {
  timeout: APP_CONFIG.apiTimeout,
  retryCount: 3,
  retryDelay: 1000,
  headers: {
    'Content-Type': 'application/json',
  },
}

// 错误消息配置
export const ERROR_MESSAGES = {
  network: '网络连接失败，请检查网络',
  timeout: '请求超时，请稍后重试',
  unauthorized: '认证失败，请检查API密钥',
  forbidden: '权限不足',
  notFound: '请求的资源不存在',
  serverError: '服务器内部错误',
  unknown: '请求失败',
}

// 开发环境检查
export const isDevelopment = APP_CONFIG.environment === 'development'
export const isProduction = APP_CONFIG.environment === 'production'
export const isDebugEnabled = APP_CONFIG.enableDebug

// 导出完整配置
export default {
  app: APP_CONFIG,
  api: API_ENDPOINTS,
  request: REQUEST_CONFIG,
  errors: ERROR_MESSAGES,
  isDevelopment,
  isProduction,
  isDebugEnabled,
}
