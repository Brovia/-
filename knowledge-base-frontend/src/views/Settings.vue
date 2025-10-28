<template>
  <div class="settings-page">
    <div class="page-header">
      <h2>系统设置</h2>
      <p>配置系统参数和API设置</p>
    </div>

    <el-row :gutter="20">
      <!-- API设置 -->
      <el-col :span="8">
        <div class="card">
          <h3>API设置</h3>
          
          <el-form :model="apiSettings" label-width="80px">
            <el-form-item label="API地址">
              <el-input 
                v-model="apiSettings.apiUrl" 
                placeholder="http://localhost:8000"
                style="width: 100%;"
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveApiSettings" :loading="savingApi" size="small">
                保存设置
              </el-button>
              <el-button @click="() => testApiConnection(true, true)" :loading="testingApi" size="small">
                测试连接
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
      
      <!-- 系统信息 -->
      <el-col :span="16">
        <div class="card">
          <h3>系统信息</h3>
          
          <el-descriptions :column="2" border>
            <el-descriptions-item label="系统版本">
              {{ systemInfo.version }}
            </el-descriptions-item>
            <el-descriptions-item label="构建时间">
              {{ systemInfo.buildTime }}
            </el-descriptions-item>
            <el-descriptions-item label="运行环境">
              {{ systemInfo.environment }}
            </el-descriptions-item>
            <el-descriptions-item label="API状态">
              <el-tag :type="systemInfo.apiStatus ? 'success' : 'danger'">
                {{ systemInfo.apiStatus ? '正常' : '异常' }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 30px;">
      <!-- 知识库设置 -->
      <el-col :span="24">
        <div class="card">
          <h3>知识库设置</h3>
          
          <el-form :model="knowledgeSettings" label-width="120px">
            <el-form-item label="默认结果数量">
              <el-input-number 
                v-model="knowledgeSettings.defaultLimit" 
                :min="1" 
                :max="100"
              />
            </el-form-item>
            
            <el-form-item label="最小相似度">
              <el-slider
                v-model="knowledgeSettings.minScore"
                :min="0"
                :max="1"
                :step="0.1"
                :format-tooltip="formatScore"
                show-input
              />
            </el-form-item>
            
            <el-form-item>
              <el-button type="primary" @click="saveKnowledgeSettings">
                保存设置
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeService, adminService, recreateApiClient } from '@/services/api'

// 响应式数据
const savingApi = ref(false)
const testingApi = ref(false)

// API设置
const apiSettings = reactive({
  apiUrl: 'http://localhost:8000'
})

// 知识库设置
const knowledgeSettings = reactive({
  defaultLimit: 10,
  minScore: 0.0
})


// 系统信息
const systemInfo = reactive({
  version: '1.0.0',
  buildTime: '2025-10-24',
  environment: 'Development',
  apiStatus: false
})


// 保存API设置
const saveApiSettings = async () => {
  try {
    savingApi.value = true
    
    // 保存到localStorage
    localStorage.setItem('apiSettings', JSON.stringify(apiSettings))
    
    // 重新创建API客户端以使用新的API地址
    recreateApiClient()
    
    ElMessage.success('API设置保存成功')
    
  } catch (error) {
    ElMessage.error('保存API设置失败')
    console.error('Save API settings error:', error)
  } finally {
    savingApi.value = false
  }
}

// 测试API连接
const testApiConnection = async (showMessage = true, showLoading = false) => {
  try {
    testingApi.value = true
    
    // 执行健康检查
    const healthResult = await adminService.healthCheck({ showLoading })
    
    const isHealthy = healthResult?.data?.status === 'healthy'
    
    systemInfo.apiStatus = isHealthy
    
    if (showMessage) {
      if (systemInfo.apiStatus) {
        ElMessage.success('API连接正常')
      } else {
        ElMessage.warning('API连接异常')
      }
    }
    
  } catch (error) {
    systemInfo.apiStatus = false
    if (showMessage) {
      ElMessage.error('API连接失败')
    }
    console.error('Test API connection error:', error)
  } finally {
    testingApi.value = false
  }
}

// 保存知识库设置
const saveKnowledgeSettings = () => {
  try {
    localStorage.setItem('knowledgeSettings', JSON.stringify(knowledgeSettings))
    ElMessage.success('知识库设置保存成功')
  } catch (error) {
    ElMessage.error('保存知识库设置失败')
    console.error('Save knowledge settings error:', error)
  }
}






// 格式化相似度分数
const formatScore = (value) => {
  return `${(value * 100).toFixed(0)}%`
}

// 加载设置
const loadSettings = () => {
  try {
    // 加载API设置
    const savedApiSettings = localStorage.getItem('apiSettings')
    if (savedApiSettings) {
      Object.assign(apiSettings, JSON.parse(savedApiSettings))
    }
    
    // 加载知识库设置
    const savedKnowledgeSettings = localStorage.getItem('knowledgeSettings')
    if (savedKnowledgeSettings) {
      Object.assign(knowledgeSettings, JSON.parse(savedKnowledgeSettings))
    }
    
    
  } catch (error) {
    console.error('Load settings error:', error)
  }
}

// 组件挂载
onMounted(async () => {
  // 加载本地设置
  loadSettings()
  
  // 加载API状态
  await testApiConnection(false, false)
})
</script>

<style lang="scss" scoped>
.settings-page {
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
  
  // 确保并排的卡片等高
  .el-row {
    .el-col {
      display: flex;
      
      .card {
        width: 100%;
        display: flex;
        flex-direction: column;
        
        // API设置表单上边距
        .el-form {
          margin-top: 30px;
        }
        
        // 系统信息表格上下居中
        .el-descriptions {
          margin-top: auto;
          margin-bottom: auto;
        }
      }
    }
  }
}

[data-theme="dark"] .settings-page {
  .page-header {
    h2 {
      color: #e5eaf3;
    }
    
    p {
      color: #c0c4cc;
    }
  }
}
</style>
