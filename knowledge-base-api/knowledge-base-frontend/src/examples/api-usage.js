/**
 * API使用示例
 * 展示如何使用新的API服务层
 */

import { knowledgeService, adminService } from '@/services/api.js'
import { useApiStore } from '@/stores/api.js'
import { handleApiResponse, handleApiError, retryRequest } from '@/utils/api-helpers.js'

// 示例1: 基本API调用
export const basicApiUsage = async () => {
  try {
    // 搜索知识库
    const searchResponse = await knowledgeService.search({
      query: '负载均衡',
      search_type: 'hybrid',
      limit: 10
    })
    
    console.log('搜索结果:', handleApiResponse(searchResponse))
  } catch (error) {
    handleApiError(error)
  }
}

// 示例2: 使用状态管理
export const apiWithStateManagement = async () => {
  const apiStore = useApiStore()
  
  try {
    apiStore.setLoading(true)
    apiStore.clearError()
    
    const response = await knowledgeService.getStats()
    const stats = handleApiResponse(response)
    
    console.log('统计信息:', stats)
  } catch (error) {
    apiStore.setError(error)
  } finally {
    apiStore.setLoading(false)
  }
}

// 示例3: 带重试的API调用
export const apiWithRetry = async () => {
  try {
    const response = await retryRequest(
      () => adminService.healthCheck(),
      3, // 重试3次
      1000 // 初始延迟1秒
    )
    
    console.log('健康检查:', handleApiResponse(response))
  } catch (error) {
    handleApiError(error, {
      customMessage: '健康检查失败，请稍后重试'
    })
  }
}

// 示例4: 文件上传
export const uploadFile = async (file) => {
  try {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await adminService.uploadDocument(formData)
    
    return handleApiResponse(response, {
      showSuccessMessage: true,
      successMessage: '文件上传成功'
    })
  } catch (error) {
    handleApiError(error, {
      customMessage: '文件上传失败'
    })
  }
}

// 示例5: 批量操作
export const batchOperations = async () => {
  const operations = [
    () => knowledgeService.getStats(),
    () => adminService.healthCheck(),
  ]
  
  try {
    const results = await Promise.allSettled(
      operations.map(op => op())
    )
    
    results.forEach((result, index) => {
      if (result.status === 'fulfilled') {
        console.log(`操作${index + 1}成功:`, handleApiResponse(result.value))
      } else {
        console.error(`操作${index + 1}失败:`, result.reason)
      }
    })
  } catch (error) {
    handleApiError(error)
  }
}

// 示例6: 智能问答
export const intelligentQA = async (question) => {
  try {
    const response = await knowledgeService.askQuestion({
      question,
      max_tokens: 1000,
      temperature: 0.7
    })
    
    return handleApiResponse(response)
  } catch (error) {
    handleApiError(error, {
      customMessage: '问答服务暂时不可用'
    })
  }
}

// 示例7: 文档管理
export const documentManagement = async () => {
  try {
    // 获取文档列表
    const documentsResponse = await adminService.getDocuments({
      page: 1,
      size: 10
    })
    
    const documents = handleApiResponse(documentsResponse)
    console.log('文档列表:', documents)
    
    // 删除第一个文档（如果存在）
    if (documents.documents && documents.documents.length > 0) {
      const firstDoc = documents.documents[0]
      const deleteResponse = await adminService.deleteDocument(firstDoc.id)
      
      console.log('删除结果:', handleApiResponse(deleteResponse, {
        showSuccessMessage: true,
        successMessage: '文档删除成功'
      }))
    }
  } catch (error) {
    handleApiError(error)
  }
}

// 示例8: 错误处理和恢复
export const errorHandlingAndRecovery = async () => {
  const apiStore = useApiStore()
  
  try {
    // 尝试执行可能失败的操作
    const response = await adminService.reindex()
    
    return handleApiResponse(response, {
      showSuccessMessage: true,
      successMessage: '索引重建成功'
    })
  } catch (error) {
    // 记录错误
    apiStore.setError(error)
    
    // 尝试恢复
    if (apiStore.stats.errorRate > 50) {
      console.warn('错误率过高，尝试重置状态')
      apiStore.reset()
    }
    
    // 重新抛出错误
    throw error
  }
}

// 示例9: 条件API调用
export const conditionalApiCall = async (condition) => {
  if (!condition) {
    console.log('跳过API调用')
    return null
  }
  
  try {
    const response = await knowledgeService.recommend({
      document_id: 'example',
      limit: 5
    })
    
    return handleApiResponse(response)
  } catch (error) {
    handleApiError(error, {
      showErrorMessage: false, // 不显示错误消息
      onError: (err, message) => {
        console.warn('推荐服务不可用:', message)
      }
    })
    return null
  }
}

// 导出所有示例
export default {
  basicApiUsage,
  apiWithStateManagement,
  apiWithRetry,
  uploadFile,
  batchOperations,
  intelligentQA,
  documentManagement,
  errorHandlingAndRecovery,
  conditionalApiCall,
}
