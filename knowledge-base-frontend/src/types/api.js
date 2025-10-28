/**
 * API类型定义
 * 定义API请求和响应的数据结构
 */

// 通用响应结构
export const ApiResponse = {
  success: true,
  data: null,
  message: '',
  timestamp: '',
}

// 分页响应结构
export const PaginatedResponse = {
  items: [],
  total: 0,
  page: 1,
  size: 10,
  pages: 0,
}

// 知识库API类型
export const KnowledgeTypes = {
  // 搜索请求
  SearchRequest: {
    query: '', // 搜索查询
    search_type: 'hybrid', // 搜索类型: vector, keyword, hybrid
    limit: 10, // 结果数量限制
    min_score: 0, // 最小相似度分数
    filters: {}, // 过滤条件
  },

  // 搜索响应
  SearchResponse: {
    results: [], // 搜索结果
    total: 0, // 总结果数
    query: '', // 原始查询
    search_type: '', // 使用的搜索类型
    processing_time: 0, // 处理时间(ms)
  },

  // 搜索结果项
  SearchResult: {
    id: '', // 文档ID
    title: '', // 文档标题
    content: '', // 内容片段
    score: 0, // 相似度分数
    metadata: {}, // 元数据
    source: '', // 来源文档
  },

  // 问答请求
  QuestionRequest: {
    question: '', // 问题
    context: [], // 上下文文档
    max_tokens: 1000, // 最大token数
    temperature: 0.7, // 温度参数
  },

  // 问答响应
  QuestionResponse: {
    answer: '', // 答案
    confidence: 0, // 置信度
    sources: [], // 来源文档
    processing_time: 0, // 处理时间
  },

  // 摘要请求
  SummarizeRequest: {
    content: '', // 要摘要的内容
    max_length: 200, // 最大长度
    style: 'default', // 摘要风格
  },

  // 摘要响应
  SummarizeResponse: {
    summary: '', // 摘要内容
    original_length: 0, // 原文长度
    summary_length: 0, // 摘要长度
    compression_ratio: 0, // 压缩比
  },

  // 推荐请求
  RecommendRequest: {
    document_id: '', // 文档ID
    limit: 5, // 推荐数量
    similarity_threshold: 0.7, // 相似度阈值
  },

  // 推荐响应
  RecommendResponse: {
    recommendations: [], // 推荐文档
    total: 0, // 推荐总数
  },

  // 统计响应
  StatsResponse: {
    total_documents: 0, // 总文档数
    total_chunks: 0, // 总块数
    indexed_documents: 0, // 已索引文档数
    last_updated: '', // 最后更新时间
  },
}

// 管理API类型
export const AdminTypes = {
  // 健康检查响应
  HealthResponse: {
    status: 'healthy', // 状态: healthy, degraded, unhealthy
    version: '', // 版本号
    uptime: 0, // 运行时间(秒)
    services: {}, // 各服务状态
    timestamp: '', // 检查时间
  },

  // 服务状态
  ServiceStatus: {
    status: 'healthy', // 状态
    message: '', // 状态消息
    last_check: '', // 最后检查时间
  },

  // 系统指标响应
  MetricsResponse: {
    cpu_usage: 0, // CPU使用率
    memory_usage: 0, // 内存使用率
    disk_usage: 0, // 磁盘使用率
    active_connections: 0, // 活跃连接数
    request_count: 0, // 请求总数
    error_count: 0, // 错误总数
  },

  // 文档信息
  DocumentInfo: {
    id: 0, // 文档ID
    filename: '', // 文件名
    title: '', // 文档标题
    size: 0, // 文件大小
    upload_time: '', // 上传时间
    last_modified: '', // 最后修改时间
    status: 'processed', // 状态: processing, processed, failed
    chunks: 0, // 分块数量
    metadata: {}, // 元数据
  },

  // 文档列表响应
  DocumentListResponse: {
    documents: [], // 文档列表
    total: 0, // 总文档数
    page: 1, // 当前页
    size: 10, // 每页大小
  },

  // 上传响应
  UploadResponse: {
    message: '', // 响应消息
    document_id: 0, // 文档ID
    filename: '', // 文件名
    size: 0, // 文件大小
  },

  // 删除响应
  DeleteResponse: {
    message: '', // 响应消息
    deleted_chunks: 0, // 删除的块数
  },

  // 重建索引响应
  ReindexResponse: {
    message: '', // 响应消息
    total_documents: 0, // 总文档数
    indexed_successfully: 0, // 成功索引数
    failed: 0, // 失败数
    processing_time: 0, // 处理时间
  },
}

// 错误类型
export const ErrorTypes = {
  // API错误
  ApiError: {
    code: '', // 错误代码
    message: '', // 错误消息
    details: {}, // 错误详情
    timestamp: '', // 错误时间
  },

  // 验证错误
  ValidationError: {
    field: '', // 字段名
    message: '', // 错误消息
    value: null, // 字段值
  },
}

// 导出所有类型
export default {
  Knowledge: KnowledgeTypes,
  Admin: AdminTypes,
  Error: ErrorTypes,
  ApiResponse,
  PaginatedResponse,
}
