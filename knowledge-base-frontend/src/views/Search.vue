<template>
  <div class="search-page">
    <div class="page-header">
      <h2>知识搜索</h2>
      <p>在知识库中搜索相关文档和内容</p>
    </div>

    <!-- 搜索表单 -->
    <div class="card">
      <el-form :model="searchForm" @submit.prevent="handleSearch">
        <el-row :gutter="20">
          <el-col :span="16">
            <el-form-item label="搜索内容">
              <el-input
                v-model="searchForm.query"
                placeholder="请输入搜索关键词..."
                @keyup.enter="handleSearch"
                clearable
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="结果数量">
              <el-select v-model="searchForm.limit" placeholder="选择结果数量">
                <el-option label="10条" :value="10" />
                <el-option label="20条" :value="20" />
                <el-option label="50条" :value="50" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="云服务商">
              <el-select v-model="searchForm.provider" placeholder="选择云服务商" clearable>
                <el-option label="腾讯云" value="腾讯云" />
                <el-option label="阿里云" value="阿里云" />
                <el-option label="火山云" value="火山云" />
                <el-option label="华为云" value="华为云" />
                <el-option label="AWS" value="AWS" />
                <el-option label="Azure" value="Azure" />
                <el-option label="GCP" value="GCP" />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="产品分类">
              <el-select v-model="searchForm.category" placeholder="选择产品分类" clearable>
                <el-option label="负载均衡" value="负载均衡" />
                <el-option label="私有网络" value="私有网络" />
                <el-option label="弹性IP" value="弹性IP" />
                <el-option label="NAT网关" value="NAT网关" />
                <el-option label="专线" value="专线" />
                <el-option label="云联网" value="云联网" />
                <el-option label="VPN" value="VPN" />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="最小相似度">
              <el-slider
                v-model="searchForm.min_score"
                :min="0"
                :max="1"
                :step="0.1"
                :format-tooltip="formatScore"
                show-input
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item>
          <el-button 
            type="primary" 
            @click="handleSearch"
            :loading="searching"
            :icon="Search"
          >
            搜索
          </el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 搜索结果 -->
    <div v-if="searchResults.length > 0" class="search-results">
      <div class="results-header">
        <h3>搜索结果</h3>
        <div class="results-info">
          <span>找到 {{ searchMeta.total }} 条结果</span>
          <span>耗时 {{ searchMeta.processing_time }}s</span>
        </div>
      </div>
      
      <div 
        v-for="(result, index) in searchResults" 
        :key="index"
        class="search-result"
        @click="viewDocument(result)"
      >
        <div class="result-title">
          <el-icon><Document /></el-icon>
          {{ result.title }}
        </div>
        
        <div class="result-content">
          {{ result.content }}
        </div>
        
        <div class="result-meta">
          <div class="meta-left">
            <el-tag size="small" type="info">{{ result.source }}</el-tag>
            <el-tag 
              v-if="result.metadata?.provider" 
              size="small" 
              type="success"
            >
              {{ result.metadata.provider }}
            </el-tag>
            <el-tag 
              v-if="result.metadata?.category" 
              size="small" 
              type="warning"
            >
              {{ result.metadata.category }}
            </el-tag>
          </div>
          
          <div class="meta-right">
            <span class="result-score">相似度: {{ (result.score * 100).toFixed(1) }}%</span>
          </div>
        </div>
        
        <!-- 高亮片段 -->
        <div v-if="result.highlight && result.highlight.length > 0" class="result-highlight">
          <div class="highlight-title">相关片段:</div>
          <div 
            v-for="(fragment, idx) in result.highlight" 
            :key="idx"
            class="highlight-fragment"
            v-html="fragment"
          />
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!searching && hasSearched" class="empty-state">
      <el-empty description="未找到相关结果">
        <el-button type="primary" @click="resetSearch">重新搜索</el-button>
      </el-empty>
    </div>

    <!-- 搜索提示 -->
    <div v-else-if="!hasSearched" class="search-tips">
      <el-alert
        title="搜索提示"
        type="info"
        :closable="false"
      >
        <template #default>
          <ul>
            <li>支持中英文关键词搜索</li>
            <li>使用语义搜索技术，理解查询意图</li>
            <li>可以通过云服务商和分类进行筛选</li>
            <li>调整相似度阈值可以控制结果精度</li>
          </ul>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Search, Document } from '@element-plus/icons-vue'
import { knowledgeService } from '@/services/api'


// 响应式数据
const searching = ref(false)
const hasSearched = ref(false)
const searchResults = ref([])
const searchMeta = ref({
  total: 0,
  processing_time: 0
})

// 搜索表单
const searchForm = reactive({
  query: '',
  limit: 10,
  provider: '',
  category: '',
  min_score: 0.0
})

// 执行搜索
const handleSearch = async () => {
  if (!searchForm.query.trim()) {
    ElMessage.warning('请输入搜索关键词')
    return
  }
  
  try {
    searching.value = true
    hasSearched.value = true
    
    // 构建搜索参数
    const params = new URLSearchParams({
      query: searchForm.query.trim(),
      limit: searchForm.limit.toString(),
      min_score: searchForm.min_score.toString()
    })
    
    // 添加过滤条件
    if (searchForm.provider) {
      params.append('provider', searchForm.provider)
    }
    if (searchForm.category) {
      params.append('category', searchForm.category)
    }
    
    // 使用封装API
    const response = await knowledgeService.search(Object.fromEntries(params))
    
    if (response && response.status === 200) {
      const data = response.data || {}
      searchResults.value = data.results || []
      searchMeta.value = {
        total: data.total || 0,
        processing_time: data.processing_time || 0
      }
      
      if (searchResults.value.length === 0) {
        ElMessage.info('未找到相关结果，请尝试其他关键词')
      } else {
        ElMessage.success(`找到 ${data.total} 条相关结果`)
      }
    } else {
      ElMessage.error('搜索失败: 未知错误')
    }
    
  } catch (error) {
    ElMessage.error('搜索失败，请稍后重试')
    console.error('Search error:', error)
  } finally {
    searching.value = false
  }
}

// 重置搜索
const resetSearch = () => {
  searchForm.query = ''
  searchForm.limit = 10
  searchForm.provider = ''
  searchForm.category = ''
  searchForm.min_score = 0.0
  
  searchResults.value = []
  hasSearched.value = false
  searchMeta.value = {
    total: 0,
    processing_time: 0
  }
}

// 查看文档详情
const viewDocument = (result) => {
  // 这里可以实现文档详情查看功能
  ElMessage.info(`查看文档: ${result.title}`)
}

// 格式化相似度分数
const formatScore = (value) => {
  return `${(value * 100).toFixed(0)}%`
}

// 组件挂载
onMounted(() => {
  // 搜索页面不需要认证
})
</script>

<style lang="scss" scoped>
.search-page {
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
  
  .search-results {
    .results-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      
      h3 {
        margin: 0;
        color: #303133;
      }
      
      .results-info {
        color: #909399;
        font-size: 14px;
        
        span {
          margin-left: 16px;
        }
      }
    }
  }
  
  .search-result {
    cursor: pointer;
    transition: all 0.3s;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    .result-title {
      display: flex;
      align-items: center;
      font-size: 16px;
      font-weight: bold;
      color: #303133;
      margin-bottom: 8px;
      
      .el-icon {
        margin-right: 8px;
        color: #409eff;
      }
    }
    
    .result-content {
      color: #606266;
      line-height: 1.6;
      margin-bottom: 12px;
      display: -webkit-box;
      -webkit-line-clamp: 3;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    
    .result-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
      
      .meta-left {
        display: flex;
        gap: 8px;
      }
      
      .meta-right {
        .result-score {
          background: #f0f9ff;
          color: #409eff;
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 12px;
        }
      }
    }
    
    .result-highlight {
      border-top: 1px solid #f0f0f0;
      padding-top: 12px;
      
      .highlight-title {
        font-size: 12px;
        color: #909399;
        margin-bottom: 8px;
      }
      
      .highlight-fragment {
        background: #fff7e6;
        border: 1px solid #ffd591;
        border-radius: 4px;
        padding: 8px;
        margin-bottom: 4px;
        font-size: 13px;
        line-height: 1.4;
      }
    }
  }
  
  .search-tips {
    .el-alert ul {
      margin: 8px 0 0 0;
      padding-left: 20px;
      
      li {
        margin-bottom: 4px;
      }
    }
  }
}

[data-theme="dark"] .search-page {
  .page-header {
    h2 {
      color: #e5eaf3;
    }
    
    p {
      color: #c0c4cc;
    }
  }
  
  .search-results .results-header {
    h3 {
      color: #e5eaf3;
    }
    
    .results-info {
      color: #909399;
    }
  }
  
  .search-result {
    .result-title {
      color: #e5eaf3;
    }
    
    .result-content {
      color: #c0c4cc;
    }
    
    .result-highlight {
      border-top-color: #434a50;
      
      .highlight-fragment {
        background: #2d2d2d;
        border-color: #555;
        color: #e5eaf3;
      }
    }
  }
}
</style>
