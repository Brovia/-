<template>
  <div class="documents-page">
    <div class="page-header">
      <h2>文档管理</h2>
      <p>管理知识库中的文档，按云厂商和产品分类组织</p>
    </div>

    <!-- 操作栏 -->
    <div class="card">
      <el-row :gutter="20" align="middle">
        <el-col :span="6">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索文档..."
            @input="handleSearch"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        
        <el-col :span="3">
          <el-select v-model="filterProvider" placeholder="选择云服务商" clearable @change="handleFilter">
            <el-option label="全部" value="" />
            <el-option label="腾讯云" value="腾讯云" />
            <el-option label="阿里云" value="阿里云" />
            <el-option label="火山云" value="火山云" />
            <el-option label="华为云" value="华为云" />
            <el-option label="AWS" value="AWS" />
            <el-option label="Azure" value="Azure" />
            <el-option label="GCP" value="GCP" />
          </el-select>
        </el-col>
        
        <el-col :span="3">
          <el-select v-model="filterCategory" placeholder="选择产品分类" clearable @change="handleFilter">
            <el-option label="全部" value="" />
            <el-option label="负载均衡" value="负载均衡" />
            <el-option label="私有网络" value="私有网络" />
            <el-option label="弹性IP" value="弹性IP" />
            <el-option label="NAT网关" value="NAT网关" />
            <el-option label="专线" value="专线" />
            <el-option label="云联网" value="云联网" />
            <el-option label="VPN" value="VPN" />
          </el-select>
        </el-col>
        
        <el-col :span="6">
          <div class="action-buttons">
            <el-button type="primary" @click="$router.push('/upload')" :icon="Upload">
              上传文档
            </el-button>
            <el-button @click="refreshDocuments" :loading="loading" :icon="Refresh">
              刷新
            </el-button>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 树形目录视图 -->
      <div class="tree-view">
        <div class="directory-tree">
          <div class="tree-header">
            <h4>云厂商目录</h4>
          </div>
          <div class="tree-content">
            <div 
              class="provider-node all-documents"
              :class="{ active: currentDirectory.name === '所有文档' }"
              @click="selectAllDocuments"
            >
              <el-icon class="provider-icon" style="color: #409eff;">
                <Document />
              </el-icon>
              <span class="provider-name">所有文档</span>
              <span class="document-count">({{ documents.length }})</span>
            </div>
            
            <div 
              v-for="provider in cloudProviders" 
              :key="provider.name"
              class="provider-section"
            >
              <div 
                class="provider-node"
                :class="{ active: currentDirectory.name === provider.name }"
                @click="toggleProvider(provider)"
              >
                <el-icon class="expand-icon" :class="{ expanded: expandedProviders.has(provider.name) }">
                  <ArrowRight />
                </el-icon>
                <el-icon class="provider-icon" :style="{ color: provider.color }">
                  <Folder />
                </el-icon>
                <span class="provider-name">{{ provider.name }}</span>
                <span class="document-count">({{ getProviderDocumentCount(provider.name) }})</span>
              </div>
              
              <!-- 产品目录 -->
              <div 
                v-if="expandedProviders.has(provider.name)" 
                class="products-list"
              >
                <div 
                  v-for="product in provider.products" 
                  :key="product.name"
                  class="product-node"
                  :class="{ active: currentDirectory.name === `${provider.name} - ${product.name}` }"
                  @click="selectProduct(provider, product)"
                >
                  <span class="product-emoji">{{ product.icon }}</span>
                  <span class="product-name">{{ product.name }}</span>
                  <span class="document-count">({{ getProductDocumentCount(provider.name, product.name) }})</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="documents-list">
          <div class="list-header">
            <div class="header-left">
              <h3>{{ currentDirectory.name || '所有文档' }}</h3>
              <span class="document-count">{{ filteredTotal }} 个文档</span>
            </div>
            <div class="header-right" v-if="selectedDocuments.length > 0">
              <span class="selected-count">已选择 {{ selectedDocuments.length }} 个文档</span>
              <el-button 
                type="danger" 
                size="small" 
                @click="batchDeleteDocuments"
                :loading="batchDeleting"
                :icon="Delete"
              >
                批量删除
              </el-button>
            </div>
          </div>
          
          <el-table
            :data="paginatedDocuments"
            v-loading="loading"
            stripe
            style="width: 100%"
            empty-text="该目录下暂无文档"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            
            <el-table-column prop="filename" label="文件名" min-width="200">
              <template #default="{ row }">
                <div class="file-info">
                  <el-icon class="file-icon"><Document /></el-icon>
                  <span class="file-name">{{ row.filename }}</span>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
            
            <el-table-column prop="provider" label="云服务商" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.provider" :type="getProviderTagType(row.provider)" size="small">
                  {{ row.provider }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="category" label="分类" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.category" type="info" size="small">
                  {{ row.category }}
                </el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="file_size" label="文件大小" width="100">
              <template #default="{ row }">
                {{ formatFileSize(row.file_size) }}
              </template>
            </el-table-column>
            
            <el-table-column prop="word_count" label="字数" width="100">
              <template #default="{ row }">
                {{ row.word_count || '-' }}
              </template>
            </el-table-column>
            
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)" size="small">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="创建时间" width="160">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="viewDocument(row)" :icon="View">
                  查看
                </el-button>
                <el-button size="small" type="danger" @click="deleteDocument(row)" :icon="Delete">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <!-- 分页组件 -->
          <div class="pagination-wrapper">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="filteredTotal"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 文档详情对话框 -->
    <el-dialog
      v-model="showDocumentDialog"
      :title="selectedDocument?.title || '文档详情'"
      width="80%"
      :before-close="closeDocumentDialog"
    >
      <div v-if="selectedDocument" class="document-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="文件名">
            {{ selectedDocument.filename }}
          </el-descriptions-item>
          <el-descriptions-item label="文件大小">
            {{ formatFileSize(selectedDocument.file_size) }}
          </el-descriptions-item>
          <el-descriptions-item label="云服务商">
            {{ selectedDocument.provider || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="分类">
            {{ selectedDocument.category || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="字数">
            {{ selectedDocument.word_count || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(selectedDocument.status)">
              {{ getStatusText(selectedDocument.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(selectedDocument.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ formatDate(selectedDocument.updated_at) }}
          </el-descriptions-item>
        </el-descriptions>
        
        <div v-if="selectedDocument.source_url" class="source-url">
          <h4>来源链接</h4>
          <el-link :href="selectedDocument.source_url" target="_blank" type="primary">
            {{ selectedDocument.source_url }}
          </el-link>
        </div>
        
        <div v-if="selectedDocument.tags && selectedDocument.tags.length > 0" class="document-tags">
          <h4>标签</h4>
          <el-tag 
            v-for="tag in selectedDocument.tags" 
            :key="tag"
            size="small"
            style="margin-right: 8px; margin-bottom: 8px;"
          >
            {{ tag }}
          </el-tag>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="closeDocumentDialog">关闭</el-button>
        <el-button type="primary" @click="searchInDocument">在知识库中搜索</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Search, Upload, Refresh, Document, View, Delete, 
  Folder, ArrowRight
} from '@element-plus/icons-vue'
import { useDashboardStore } from '@/stores/dashboard'
import { adminService } from '@/services/api'

const router = useRouter()
const dashboardStore = useDashboardStore()

// 响应式数据
const loading = ref(false)
const documents = ref([])
const searchKeyword = ref('')
const filterProvider = ref('')
const filterCategory = ref('')
const showDocumentDialog = ref(false)
const selectedDocument = ref(null)

// 批量操作相关
const selectedDocuments = ref([])
const batchDeleting = ref(false)

// 视图模式 - 只使用树形视图
const viewMode = ref('tree')

// 目录树相关
const currentDirectory = ref({ name: '所有文档', path: [] })

// 标准产品分类
const standardProductCategories = ref([
  { name: '负载均衡', icon: '⚖️', color: '#52c41a' },
  { name: '私有网络', icon: '🌐', color: '#1890ff' },
  { name: '弹性IP', icon: '🔗', color: '#722ed1' },
  { name: 'NAT网关', icon: '🚪', color: '#fa8c16' },
  { name: '专线', icon: '🔌', color: '#eb2f96' },
  { name: '云联网', icon: '🌍', color: '#13c2c2' },
  { name: 'VPN', icon: '🔒', color: '#f5222d' }
])

// 云厂商数据
const cloudProviders = ref([
  { 
    name: '腾讯云', 
    color: '#006EFF',
    products: standardProductCategories.value
  },
  { 
    name: '阿里云', 
    color: '#FF6A00',
    products: standardProductCategories.value
  },
  { 
    name: '火山云', 
    color: '#FF4D4F',
    products: standardProductCategories.value
  },
  { 
    name: '华为云', 
    color: '#FF6900',
    products: standardProductCategories.value
  },
  { 
    name: 'AWS', 
    color: '#FF9900',
    products: standardProductCategories.value
  },
  { 
    name: 'Azure', 
    color: '#0078D4',
    products: standardProductCategories.value
  },
  { 
    name: 'GCP', 
    color: '#4285F4',
    products: standardProductCategories.value
  }
])

// 展开状态
const expandedProviders = ref(new Set())

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const totalDocuments = ref(0)

// 计算属性 - 过滤后的文档
const filteredDocuments = computed(() => {
  let filtered = documents.value
  
  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(doc => 
      doc.filename.toLowerCase().includes(keyword) ||
      doc.title.toLowerCase().includes(keyword) ||
      (doc.provider && doc.provider.toLowerCase().includes(keyword)) ||
      (doc.category && doc.category.toLowerCase().includes(keyword))
    )
  }
  
  // 云服务商过滤
  if (filterProvider.value) {
    filtered = filtered.filter(doc => doc.provider === filterProvider.value)
  }
  
  // 产品分类过滤
  if (filterCategory.value) {
    filtered = filtered.filter(doc => doc.category === filterCategory.value)
  }
  
  // 树形视图下的目录过滤
  if (currentDirectory.value.path.length > 0) {
    const selectedProvider = currentDirectory.value.path[0]
    if (currentDirectory.value.path.length === 1) {
      // 只选择了云厂商
      filtered = filtered.filter(doc => doc.provider === selectedProvider)
    } else if (currentDirectory.value.path.length === 2) {
      // 选择了云厂商和产品
      const selectedProduct = currentDirectory.value.path[1]
      filtered = filtered.filter(doc => 
        doc.provider === selectedProvider && doc.category === selectedProduct
      )
    }
  }
  
  return filtered
})

// 计算属性 - 分页后的文档（用于实际渲染）
const paginatedDocuments = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredDocuments.value.slice(start, end)
})

// 计算属性 - 过滤后的总数
const filteredTotal = computed(() => filteredDocuments.value.length)

// 获取文档列表
const fetchDocuments = async (showGlobalLoading = false) => {
  try {
    loading.value = true
    
    // 使用封装的API获取文档列表，传递分页参数获取所有文档
    const response = await adminService.getDocuments({
      skip: 0,
      limit: 100000  // 增加限制以获取所有文档
    }, { 
      showLoading: showGlobalLoading 
    })
    if (response && response.status === 200) {
      const data = response.data || {}
      documents.value = data.documents || []
      totalDocuments.value = data.total || 0
      
      console.log('Fetched documents:', documents.value.length, '个文档，总计:', totalDocuments.value)   
    } else {
      const errorData = await response.json()
      ElMessage.error(`获取文档列表失败: ${errorData.detail || '未知错误'}`)
      documents.value = []
      totalDocuments.value = 0
    }
    
  } catch (error) {
    ElMessage.error('获取文档列表失败')
    console.error('Fetch documents error:', error)
    documents.value = []
    totalDocuments.value = 0
  } finally {
    loading.value = false
  }
}


// 选择所有文档
const selectAllDocuments = () => {
  currentDirectory.value = {
    name: '所有文档',
    path: []
  }
  // 清空选择状态
  selectedDocuments.value = []
}

// 切换云厂商展开/折叠
const toggleProvider = (provider) => {
  if (expandedProviders.value.has(provider.name)) {
    expandedProviders.value.delete(provider.name)
  } else {
    expandedProviders.value.add(provider.name)
  }
  
  // 选择云厂商
  currentDirectory.value = {
    name: provider.name,
    path: [provider.name]
  }
  // 清空选择状态
  selectedDocuments.value = []
}

// 选择产品
const selectProduct = (provider, product) => {
  currentDirectory.value = {
    name: `${provider.name} - ${product.name}`,
    path: [provider.name, product.name]
  }
  // 清空选择状态
  selectedDocuments.value = []
}

// 缓存的文档统计（避免重复计算）
const documentStats = computed(() => {
  const stats = {
    byProvider: {},
    byProduct: {}
  }
  
  documents.value.forEach(doc => {
    // 按云服务商统计
    if (doc.provider) {
      stats.byProvider[doc.provider] = (stats.byProvider[doc.provider] || 0) + 1
    }
    
    // 按产品统计
    if (doc.provider && doc.category) {
      const key = `${doc.provider}:${doc.category}`
      stats.byProduct[key] = (stats.byProduct[key] || 0) + 1
    }
  })
  
  return stats
})

// 获取云厂商文档数量（使用缓存）
const getProviderDocumentCount = (providerName) => {
  return documentStats.value.byProvider[providerName] || 0
}

// 获取产品文档数量（使用缓存）
const getProductDocumentCount = (providerName, productName) => {
  const key = `${providerName}:${productName}`
  return documentStats.value.byProduct[key] || 0
}

// 刷新文档列表
const refreshDocuments = async () => {
  await fetchDocuments(true) // 显示加载遮罩
  ElMessage.success('文档列表已刷新')
}

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1
  // 清空选择状态
  selectedDocuments.value = []
}

// 过滤处理
const handleFilter = () => {
  currentPage.value = 1
  // 清空选择状态
  selectedDocuments.value = []
}

// 查看文档
const viewDocument = (document) => {
  selectedDocument.value = document
  showDocumentDialog.value = true
}

// 关闭文档对话框
const closeDocumentDialog = () => {
  showDocumentDialog.value = false
  selectedDocument.value = null
}

// 删除文档
const deleteDocument = async (document) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档 "${document.filename}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 使用封装的API
    const response = await adminService.deleteDocument(document.id)
    if (response && response.status === 200) {
      const data = response.data || {}
      ElMessage.success(`文档删除成功: ${data.filename}`)
      // 标记仪表盘需要刷新数据
      dashboardStore.markForRefresh()
      // 触发全局事件通知仪表盘数据变化
      window.dispatchEvent(new CustomEvent('dashboard-data-changed'))
      await fetchDocuments(false) // 静默刷新
    } else {
      ElMessage.error('删除文档失败: 未知错误')
    }
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除文档失败')
      console.error('Delete document error:', error)
    }
  }
}

// 在知识库中搜索
const searchInDocument = () => {
  if (selectedDocument.value) {
    closeDocumentDialog()
    router.push({
      path: '/search',
      query: { q: selectedDocument.value.title }
    })
  }
}

// 分页处理
const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  // 清空选择状态
  selectedDocuments.value = []
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  // 清空选择状态
  selectedDocuments.value = []
}

// 批量操作相关函数
const handleSelectionChange = (selection) => {
  selectedDocuments.value = selection
}

const batchDeleteDocuments = async () => {
  if (selectedDocuments.value.length === 0) {
    ElMessage.warning('请先选择要删除的文档')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedDocuments.value.length} 个文档吗？此操作不可恢复。`,
      '确认批量删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    batchDeleting.value = true
    
    // 批量删除文档
    const deletePromises = selectedDocuments.value.map(doc => 
      adminService.deleteDocument(doc.id)
    )
    
    const results = await Promise.allSettled(deletePromises)
    
    // 统计删除结果
    let successCount = 0
    let failCount = 0
    
    results.forEach((result, index) => {
      if (result.status === 'fulfilled' && result.value && result.value.status === 200) {
        successCount++
      } else {
        failCount++
        console.error(`删除文档失败: ${selectedDocuments.value[index].filename}`, result.reason)
      }
    })
    
    if (successCount > 0) {
      ElMessage.success(`成功删除 ${successCount} 个文档`)
      // 标记仪表盘需要刷新数据
      dashboardStore.markForRefresh()
      // 触发全局事件通知仪表盘数据变化
      window.dispatchEvent(new CustomEvent('dashboard-data-changed'))
      await fetchDocuments(false) // 静默刷新
    }
    
    if (failCount > 0) {
      ElMessage.error(`${failCount} 个文档删除失败`)
    }
    
    // 清空选择
    selectedDocuments.value = []
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
      console.error('Batch delete error:', error)
    }
  } finally {
    batchDeleting.value = false
  }
}

// 工具函数
const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

const getProviderTagType = (provider) => {
  const types = {
    '腾讯云': 'primary',
    '阿里云': 'success',
    '火山云': 'danger',
    '华为云': 'danger',
    'AWS': 'warning',
    'Azure': 'info',
    'GCP': 'info'
  }
  return types[provider] || 'info'
}

const getStatusTagType = (status) => {
  const types = {
    'pending': 'info',
    'processing': 'warning',
    'processed': 'success',
    'failed': 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    'pending': '待处理',
    'processing': '处理中',
    'processed': '已处理',
    'failed': '处理失败'
  }
  return texts[status] || '未知'
}

// 组件挂载
onMounted(async () => {
  // 加载文档列表
  await fetchDocuments(false)
})
</script>

<style lang="scss" scoped>
.documents-page {
  .page-header {
    margin-bottom: 20px;
    
    h2 {
      margin-bottom: 8px;
      color: #303133;
    }
    
    p {
      color: #606266;
      margin: 0;
    }
  }
  
  .action-buttons {
    display: flex;
    gap: 10px;
    justify-content: flex-end;
  }
  
  .main-content {
    margin-top: 20px;
  }
  
  .tree-view {
    display: flex;
    gap: 20px;
    min-height: 600px;
    
    .directory-tree {
      width: 300px;
      background: #fff;
      border: 1px solid #e4e7ed;
      border-radius: 6px;
      padding: 16px;
      
      .tree-header {
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid #e4e7ed;
        
        h4 {
          margin: 0;
          color: #303133;
          font-size: 16px;
          font-weight: 600;
        }
      }
      
      .tree-content {
        .provider-section {
          margin-bottom: 4px;
          
          .provider-node {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            
            &:hover {
              background-color: #f5f7fa;
            }
            
            &.active {
              background-color: #e6f7ff;
              border: 1px solid #91d5ff;
              
              .provider-name {
                color: #1890ff;
                font-weight: 600;
              }
            }
            
            .expand-icon {
              margin-right: 8px;
              font-size: 12px;
              transition: transform 0.2s;
              
              &.expanded {
                transform: rotate(90deg);
              }
            }
            
            .provider-icon {
              margin-right: 12px;
              font-size: 18px;
            }
            
            .provider-name {
              flex: 1;
              font-weight: 500;
              color: #303133;
            }
            
            .document-count {
              color: #909399;
              font-size: 12px;
            }
          }
          
          .products-list {
            margin-left: 20px;
            margin-top: 4px;
            
            .product-node {
              display: flex;
              align-items: center;
              padding: 8px 16px;
              margin-bottom: 2px;
              border-radius: 4px;
              cursor: pointer;
              transition: all 0.2s;
              
              &:hover {
                background-color: #f5f7fa;
              }
              
              &.active {
                background-color: #e6f7ff;
                border: 1px solid #91d5ff;
                
                .product-name {
                  color: #1890ff;
                  font-weight: 600;
                }
              }
              
              .product-emoji {
                margin-right: 12px;
                font-size: 16px;
              }
              
              .product-name {
                flex: 1;
                font-size: 14px;
                color: #606266;
              }
              
              .document-count {
                color: #909399;
                font-size: 11px;
              }
            }
          }
        }
      }
    }
    
    .documents-list {
      flex: 1;
      background: #fff;
      border: 1px solid #e4e7ed;
      border-radius: 6px;
      padding: 16px;
      
      .list-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid #e4e7ed;
        
        .header-left {
          display: flex;
          align-items: center;
          gap: 12px;
          
          h3 {
            margin: 0;
            color: #303133;
            font-size: 16px;
          }
          
          .document-count {
            color: #909399;
            font-size: 14px;
          }
        }
        
        .header-right {
          display: flex;
          align-items: center;
          gap: 12px;
          
          .selected-count {
            color: #409eff;
            font-size: 14px;
            font-weight: 500;
          }
        }
      }
    }
  }
  
  
  .file-info {
    display: flex;
    align-items: center;
    
    .file-icon {
      margin-right: 8px;
      color: #409eff;
    }
    
    .file-name {
      font-weight: 500;
    }
  }
  
  .pagination-wrapper {
    margin-top: 20px;
    display: flex;
    justify-content: center;
  }
  
  .document-detail {
    .source-url {
      margin-top: 20px;
      
      h4 {
        margin-bottom: 8px;
        color: #303133;
      }
    }
    
    .document-tags {
      margin-top: 20px;
      
      h4 {
        margin-bottom: 8px;
        color: #303133;
      }
    }
  }
  
}

[data-theme="dark"] .documents-page {
  .page-header {
    h2 {
      color: #e5eaf3;
    }
    
    p {
      color: #c0c4cc;
    }
  }
  
  .document-detail {
    .source-url h4,
    .document-tags h4 {
      color: #e5eaf3;
    }
  }
}
</style>
