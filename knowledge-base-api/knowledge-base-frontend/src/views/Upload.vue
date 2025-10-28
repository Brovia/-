<template>
  <div class="upload-page">
    <div class="page-header">
      <h2>文档上传</h2>
      <p>支持上传Markdown格式的文档到知识库</p>
    </div>

    <el-row :gutter="20">
      <!-- 上传区域 -->
      <el-col :span="16">
        <div class="card">
          <h3>文件上传</h3>
          
          <!-- 文档元数据设置 -->
          <div class="metadata-section">
            <h4>文档信息</h4>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="云服务商" required>
                  <el-select v-model="documentMetadata.provider" placeholder="请选择云服务商" style="width: 100%">
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
              <el-col :span="12">
                <el-form-item label="上传模式">
                  <el-radio-group v-model="uploadMode" @change="onUploadModeChange">
                    <el-radio label="file">单个/多个文件</el-radio>
                    <el-radio label="folder">文件夹</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="产品分类" required>
                  <el-select v-model="documentMetadata.category" placeholder="请选择产品分类" style="width: 100%">
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
              <el-col :span="12">
                <el-form-item label="文档标题">
                  <el-input v-model="documentMetadata.title" placeholder="请输入文档标题（可选）" />
                </el-form-item>
              </el-col>
            </el-row>
          </div>
          
          <!-- 文件上传区域 -->
          <div v-show="uploadMode === 'file'">
            <el-upload
              ref="uploadRef"
              class="upload-dragger"
              drag
              :action="uploadUrl"
              :headers="uploadHeaders"
              :data="uploadData"
              :before-upload="beforeUpload"
              :on-success="onUploadSuccess"
              :on-error="onUploadError"
              :on-progress="onUploadProgress"
              :file-list="fileList"
              :auto-upload="false"
              :on-change="onFileChange"
              accept=".md,.markdown"
              multiple
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持 .md/.doc/.docx/.pdf/.txt/.xlsx/.xls/.pptx/.ppt 格式，且不超过 10MB
                </div>
              </template>
            </el-upload>
          </div>
          
          <!-- 文件夹上传区域 -->
          <div v-show="uploadMode === 'folder'" class="folder-upload-container">
            <div class="upload-dragger" @click="selectFolder">
              <el-icon class="el-icon--upload"><folder-opened /></el-icon>
              <div class="el-upload__text">
                <em>点击选择文件夹</em>
              </div>
              <div class="el-upload__tip">
                自动上传文件夹中所有文档<br>
              </div>
            </div>
            <input 
              ref="folderInputRef" 
              type="file" 
              webkitdirectory 
              directory 
              multiple 
              accept=".md,.markdown"
              style="display: none;" 
              @change="onFolderSelected"
            />
            <!-- 显示已选择的文件夹信息 -->
            <div v-if="selectedFolderName" class="folder-info">
              <el-alert type="success" :closable="false">
                <template #title>
                  <div class="folder-name">
                    <el-icon><folder /></el-icon>
                    <span>已选择文件夹: {{ selectedFolderName }}</span>
                  </div>
                  <div class="folder-stats">
                    找到 {{ folderFileCount }} 个支持的文档文件
                  </div>
                </template>
              </el-alert>
            </div>
          </div>
          
          <div class="upload-actions">
            <el-button 
              type="primary" 
              @click="submitUpload"
              :disabled="buttonDisabled"
            >
              添加到上传队列
            </el-button>
            <el-button @click="clearFiles">清空当前选择</el-button>
          </div>
          
        </div>
      </el-col>
      
      <!-- 上传进度和结果 -->
      <el-col :span="8">
        <div class="card">
          <h3>上传任务 ({{ uploadTasks.length }})</h3>
          
          <!-- 上传任务列表 -->
          <div v-if="uploadTasks.length > 0" class="upload-tasks">
            <div 
              v-for="task in uploadTasks" 
              :key="task.id"
              class="task-item"
              :class="{ 'task-completed': task.status === 'completed', 'task-error': task.status === 'error' }"
            >
              <div class="task-header">
                <div class="task-info">
                  <el-icon v-if="task.status === 'uploading'"><Loading /></el-icon>
                  <el-icon v-else-if="task.status === 'completed'" style="color: #67c23a;"><CircleCheck /></el-icon>
                  <el-icon v-else-if="task.status === 'error'" style="color: #f56c6c;"><CircleClose /></el-icon>
                  <el-icon v-else><Document /></el-icon>
                  <span class="task-name">{{ task.name }}</span>
                </div>
                <el-button 
                  v-if="task.status === 'completed' || task.status === 'error'"
                  type="text" 
                  size="small"
                  @click="removeTask(task.id)"
                >
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
              
              <div class="task-metadata">
                <el-tag size="small" type="primary">{{ task.provider }}</el-tag>
                <el-tag size="small" type="info">{{ task.category }}</el-tag>
                <span class="file-count">{{ task.fileCount }} 个文件</span>
              </div>
              
              <div v-if="task.status === 'uploading'" class="task-progress">
                <el-progress 
                  :percentage="task.progress" 
                  :status="task.progress === 100 ? 'success' : ''"
                />
                <p class="progress-text">{{ task.progressText }}</p>
              </div>
              
              <div v-else-if="task.status === 'completed'" class="task-result success">
                <p>✓ 上传完成: {{ task.successCount }}/{{ task.fileCount }} 文件成功</p>
              </div>
              
              <div v-else-if="task.status === 'error'" class="task-result error">
                <p>✗ 上传失败: {{ task.errorMessage }}</p>
              </div>
              
              <!-- 展开详细结果 -->
              <div v-if="task.results && task.results.length > 0" class="task-details">
                <el-collapse>
                  <el-collapse-item title="查看详情" :name="task.id">
                    <div 
                      v-for="(result, index) in task.results" 
                      :key="index"
                      class="result-item"
                    >
                      <div class="result-header">
                        <span class="filename">{{ result.filename }}</span>
                        <el-tag 
                          :type="result.success ? 'success' : 'danger'"
                          size="small"
                        >
                          {{ result.success ? '成功' : '失败' }}
                        </el-tag>
                      </div>
                      <div v-if="result.message" class="result-message">
                        {{ result.message }}
                      </div>
                    </div>
                  </el-collapse-item>
                </el-collapse>
              </div>
            </div>
          </div>
          
          <!-- 上传提示 -->
          <div v-else class="upload-tips">
            <el-alert
              title="上传提示"
              type="info"
              :closable="false"
            >
              <template #default>
              <ul>
                <li>支持批量上传多种格式文档（.md/.doc/.docx/.pdf/.txt/.xlsx/.xls/.pptx/.ppt）</li>
                <li>支持直接上传包含多级子文件夹的目录</li>
                <li>支持多个文件夹同时上传，互不影响</li>
                <li>文件会自动解析并建立索引</li>
                <li>上传完成后可立即搜索</li>
              </ul>
              </template>
            </el-alert>
          </div>
        </div>
      </el-col>
    </el-row>
    
    <!-- 文档预览 -->
    <div v-if="previewContent" class="card">
      <h3>文档预览</h3>
      <div class="preview-content">
        <div v-html="previewContent"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  UploadFilled, FolderOpened, Folder, Loading, 
  CircleCheck, CircleClose, Document, Close 
} from '@element-plus/icons-vue'
import { useDashboardStore } from '@/stores/dashboard'
import { adminService } from '@/services/api'

const dashboardStore = useDashboardStore()

// 响应式数据
const uploadRef = ref()
const folderInputRef = ref()
const fileList = ref([])
const uploadTasks = ref([]) // 上传任务列表
const previewContent = ref('')
const uploadMode = ref('file') // 'file' 或 'folder'
const selectedFolderName = ref('')
const folderFileCount = ref(0)
const folderFiles = ref([]) // 存储文件夹中的文件及其相对路径
const documentMetadata = ref({
  provider: '',
  category: '',
  title: ''
})

// 任务ID计数器
let taskIdCounter = 0

// 计算属性
const uploadUrl = computed(() => '/api/v1/admin/documents/upload')
const uploadHeaders = computed(() => {
  return {}
})
const uploadData = computed(() => ({
  provider: documentMetadata.value.provider,
  category: documentMetadata.value.category,
  title: documentMetadata.value.title
}))

// 按钮状态计算属性 - 移除 uploading 依赖，允许在上传过程中继续添加任务
const buttonDisabled = computed(() => {
  const hasFiles = uploadMode.value === 'file' 
    ? fileList.value.length > 0 
    : folderFiles.value.length > 0
  
  return !hasFiles || 
         !documentMetadata.value.provider || 
         !documentMetadata.value.category
})

// 支持的文件格式
const supportedFormats = [
  '.md', '.markdown', '.doc', '.docx', '.pdf', '.txt', 
  '.xlsx', '.xls', '.pptx', '.ppt'
]

// 检查文件格式是否支持
const isSupportedFormat = (filename) => {
  const ext = filename.toLowerCase().substring(filename.lastIndexOf('.'))
  return supportedFormats.includes(ext)
}

// 提取文件名（不包含扩展名）作为标题
const getFileNameWithoutExtension = (filename) => {
  const lastDotIndex = filename.lastIndexOf('.')
  return lastDotIndex > 0 ? filename.substring(0, lastDotIndex) : filename
}

// 上传前检查
const beforeUpload = (file) => {
  if (!isSupportedFormat(file.name)) {
    ElMessage.error(`不支持的文件格式！支持的格式：${supportedFormats.join(', ')}`)
    return false
  }
  
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    ElMessage.error('文件大小不能超过 10MB!')
    return false
  }
  
  return true
}

// 上传模式切换
const onUploadModeChange = () => {
  // 清空当前选择
  if (uploadMode.value === 'file') {
    folderFiles.value = []
    selectedFolderName.value = ''
    folderFileCount.value = 0
  } else {
    uploadRef.value?.clearFiles()
    fileList.value = []
  }
}

// 选择文件夹
const selectFolder = () => {
  folderInputRef.value?.click()
}

// 文件夹选择处理
const onFolderSelected = async (event) => {
  const files = event.target.files
  if (!files || files.length === 0) {
    return
  }
  
  // 过滤出支持的文档文件
  const supportedFiles = Array.from(files).filter(file => 
    isSupportedFormat(file.name)
  )
  
  if (supportedFiles.length === 0) {
    ElMessage.warning(`所选文件夹中没有找到支持的文档文件。支持的格式：${supportedFormats.join(', ')}`)
    return
  }
  
  // 获取文件夹名称（取第一个文件的路径中的顶级文件夹）
  const firstFilePath = supportedFiles[0].webkitRelativePath || supportedFiles[0].name
  const folderName = firstFilePath.split('/')[0] || '未知文件夹'
  
  // 存储文件及其相对路径
  folderFiles.value = supportedFiles.map(file => ({
    file: file,
    relativePath: file.webkitRelativePath || file.name,
    name: file.name,
    title: getFileNameWithoutExtension(file.name)
  }))
  
  selectedFolderName.value = folderName
  folderFileCount.value = supportedFiles.length
  
  ElMessage.success(`已选择文件夹: ${folderName}，找到 ${supportedFiles.length} 个支持的文档文件`)
}

// 创建新的上传任务
const createUploadTask = (filesToUpload, metadata, taskName) => {
  const taskId = ++taskIdCounter
  const task = {
    id: taskId,
    name: taskName,
    provider: metadata.provider,
    category: metadata.category,
    fileCount: filesToUpload.length,
    status: 'uploading', // uploading, completed, error
    progress: 0,
    progressText: '准备上传...',
    successCount: 0,
    results: [],
    errorMessage: ''
  }
  
  // 添加任务到列表
  uploadTasks.value.unshift(task)
  
  // 异步执行上传
  executeUploadTask(task, filesToUpload, metadata)
  
  return task
}

// 执行上传任务
const executeUploadTask = async (task, filesToUpload, metadata) => {
  try {
    const totalFiles = filesToUpload.length
    let completedFiles = 0
    
    // 开始上传
    task.progressText = `开始上传 ${totalFiles} 个文件...`
    
    // 逐个上传文件
    for (const fileItem of filesToUpload) {
      try {
        const displayName = fileItem.relativePath || fileItem.name
        task.progressText = `正在上传: ${displayName} (${completedFiles + 1}/${totalFiles})`
        
        const formData = new FormData()
        formData.append('file', fileItem.file)
        formData.append('provider', metadata.provider)
        formData.append('category', metadata.category)
        
        // 使用文件名作为默认标题（不包含扩展名）
        const title = fileItem.title || getFileNameWithoutExtension(fileItem.file.name)
        formData.append('title', title)
        
        // 如果是文件夹上传，添加相对路径参数
        if (fileItem.relativePath) {
          // 移除根文件夹名，只保留子路径
          const pathParts = fileItem.relativePath.split('/')
          if (pathParts.length > 1) {
            // 去掉第一级目录（文件夹名），保留子目录结构
            const subPath = pathParts.slice(1).join('/')
            formData.append('relative_path', subPath)
          }
        }
        
        // 使用封装的API
        const response = await adminService.uploadDocument(formData)
        
        if (response && response.status === 200) {
          const data = response.data || {}
          task.results.push({
            filename: displayName,
            success: true,
            message: `上传成功，文档大小: ${data.size} 字节`
          })
          task.successCount++
        } else {
          task.results.push({
            filename: displayName,
            success: false,
            message: '上传失败'
          })
        }
        
      } catch (error) {
        task.results.push({
          filename: fileItem.relativePath || fileItem.name,
          success: false,
          message: '网络错误或上传失败'
        })
      }
      
      // 更新进度 - 无论成功还是失败都要更新
      completedFiles++
      const newProgress = Math.round((completedFiles / totalFiles) * 100)
      task.progress = newProgress
      
      // 调试日志
      console.log(`任务 ${task.name}: 进度 ${newProgress}% (${completedFiles}/${totalFiles})`)
      
      // 强制触发响应式更新
      uploadTasks.value = [...uploadTasks.value]
      
      // 添加短暂延迟以便用户能看到进度变化
      await new Promise(resolve => setTimeout(resolve, 100))
    }
    
    // 任务完成
    task.status = 'completed'
    task.progressText = `上传完成: ${task.successCount}/${totalFiles} 文件成功`
    
    // 显示结果统计
    const failCount = task.results.length - task.successCount
    
    // 如果有文件上传成功，标记仪表盘需要刷新数据
    if (task.successCount > 0) {
      dashboardStore.markForRefresh()
      // 触发全局事件通知仪表盘数据变化
      window.dispatchEvent(new CustomEvent('dashboard-data-changed'))
      ElMessage.success(`任务"${task.name}"完成: 成功上传 ${task.successCount}/${totalFiles} 个文件`)
    }
    
    if (failCount > 0) {
      ElMessage.warning(`任务"${task.name}": ${failCount} 个文件上传失败`)
    }
    
  } catch (error) {
    task.status = 'error'
    task.errorMessage = '上传过程中发生错误'
    ElMessage.error(`任务"${task.name}"失败: ${task.errorMessage}`)
    console.error('Upload task error:', error)
  }
}

// 开始上传 - 创建新任务
const submitUpload = async () => {
  // 根据上传模式获取文件列表
  const filesToUpload = uploadMode.value === 'file' 
    ? fileList.value.map(f => ({ 
        file: f.raw || f, 
        relativePath: null, 
        name: f.name,
        title: getFileNameWithoutExtension(f.name)
      }))
    : folderFiles.value
  
  if (filesToUpload.length === 0) {
    ElMessage.warning('请先选择文件或文件夹')
    return
  }
  
  if (!documentMetadata.value.provider) {
    ElMessage.warning('请选择云服务商')
    return
  }
  
  if (!documentMetadata.value.category) {
    ElMessage.warning('请选择产品分类')
    return
  }
  
  // 创建任务名称
  const taskName = uploadMode.value === 'file'
    ? (filesToUpload.length === 1 
        ? filesToUpload[0].name 
        : `${filesToUpload.length} 个文件`)
    : selectedFolderName.value || '文件夹上传'
  
  // 保存当前元数据
  const metadata = { ...documentMetadata.value }
  
  // 创建上传任务（异步执行）
  createUploadTask(filesToUpload, metadata, taskName)
  
  // 清空当前选择，允许用户继续选择其他文件/文件夹
  clearFiles()
  
  ElMessage.success(`已添加上传任务: ${taskName}`)
}

// 重建索引
const rebuildIndex = async () => {
  try {
    ElMessage.info('正在重建索引，请稍候...')
    const response = await adminService.reindex()
    const data = response?.data || {}
    // 标记仪表盘需要刷新数据
    dashboardStore.markForRefresh()
    // 触发全局事件通知仪表盘数据变化
    window.dispatchEvent(new CustomEvent('dashboard-data-changed'))
    ElMessage.success(`索引重建完成！成功处理 ${data.indexed_successfully || 0} 个文档`)
  } catch (error) {
    ElMessage.error('索引重建失败')
    console.error('Rebuild index error:', error)
  }
}

// 上传成功回调
const onUploadSuccess = (response, file) => {
  console.log('Upload success:', response)
}

// 上传失败回调
const onUploadError = (error, file) => {
  console.error('Upload error:', error)
}

// 上传进度回调
const onUploadProgress = (event, file) => {
  // 这个回调在手动上传时可能不会被调用
}

// 文件列表变化回调
const onFileChange = (file, fileListParam) => {
  // 更新文件列表状态
  fileList.value = fileListParam
}

// 删除任务
const removeTask = (taskId) => {
  const index = uploadTasks.value.findIndex(task => task.id === taskId)
  if (index !== -1) {
    uploadTasks.value.splice(index, 1)
  }
}

// 清空文件列表
const clearFiles = () => {
  if (uploadMode.value === 'file') {
    uploadRef.value?.clearFiles()
    fileList.value = []
  } else {
    folderFiles.value = []
    selectedFolderName.value = ''
    folderFileCount.value = 0
    if (folderInputRef.value) {
      folderInputRef.value.value = ''
    }
  }
  previewContent.value = ''
  // 重置元数据
  documentMetadata.value = {
    provider: '',
    category: '',
    title: ''
  }
}

// 预览文件内容
const previewFile = (file) => {
  if (file.raw) {
    const reader = new FileReader()
    reader.onload = (e) => {
      // 简单的Markdown预览（实际项目中可以使用marked.js等库）
      previewContent.value = e.target.result
    }
    reader.readAsText(file.raw)
  }
}

// 组件挂载
onMounted(() => {
  // 组件初始化
})
</script>

<style lang="scss" scoped>
.upload-page {
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
  
  .metadata-section {
    margin-bottom: 20px;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
    
    h4 {
      margin-bottom: 16px;
      color: #303133;
      font-size: 16px;
      font-weight: 600;
    }
  }
  
  .upload-dragger {
    margin-bottom: 20px;
  }
  
  .folder-upload-container {
    margin-bottom: 20px;
    
    .upload-dragger {
      position: relative;
      width: 100%;
      border: 1px dashed #d9d9d9;
      border-radius: 6px;
      background-color: #fafafa;
      cursor: pointer;
      transition: all 0.3s;
      overflow: hidden;
      padding: 40px 20px;
      text-align: center;
      
      .el-icon--upload {
        font-size: 67px;
        color: #c0c4cc;
        margin-bottom: 16px;
        line-height: 50px;
      }
      
      .el-upload__text {
        color: #606266;
        font-size: 14px;
        line-height: 1.5;
        
        em {
          color: #409eff;
          font-style: normal;
        }
      }
      
      .el-upload__tip {
        font-size: 12px;
        color: #909399;
        margin-top: 7px;
        line-height: 1.5;
      }
      
      &:hover {
        border-color: #409eff;
        background-color: #f5f7fa;
        
        .el-icon--upload {
          color: #409eff;
        }
      }
    }
    
    .folder-info {
      margin-top: 16px;
      
      .folder-name {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 8px;
        
        .el-icon {
          color: #409eff;
        }
      }
      
      .folder-stats {
        font-size: 13px;
        color: #606266;
        margin-top: 4px;
      }
    }
  }
  
  .upload-actions {
    text-align: center;
    
    .el-button {
      margin: 0 8px;
    }
  }
  
  
  .upload-tasks {
    max-height: 600px;
    overflow-y: auto;
    
    .task-item {
      border: 1px solid #e4e7ed;
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 16px;
      background: #fafafa;
      transition: all 0.3s;
      
      &.task-completed {
        background: #f0f9ff;
        border-color: #b3e5fc;
      }
      
      &.task-error {
        background: #fff5f5;
        border-color: #ffcdd2;
      }
      
      .task-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        
        .task-info {
          display: flex;
          align-items: center;
          gap: 8px;
          flex: 1;
          
          .el-icon {
            font-size: 18px;
          }
          
          .task-name {
            font-weight: 600;
            color: #303133;
            font-size: 14px;
          }
        }
      }
      
      .task-metadata {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
        
        .file-count {
          color: #909399;
          font-size: 12px;
        }
      }
      
      .task-progress {
        margin-top: 12px;
        
        .progress-text {
          margin-top: 8px;
          color: #606266;
          font-size: 12px;
        }
      }
      
      .task-result {
        margin-top: 12px;
        padding: 8px 12px;
        border-radius: 4px;
        
        &.success {
          background: #e8f5e9;
          color: #2e7d32;
        }
        
        &.error {
          background: #ffebee;
          color: #c62828;
        }
        
        p {
          margin: 0;
          font-size: 13px;
        }
      }
      
      .task-details {
        margin-top: 12px;
        
        .result-item {
          border: 1px solid #e4e7ed;
          border-radius: 4px;
          padding: 8px;
          margin-bottom: 6px;
          background: #fff;
          
          .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
            
            .filename {
              font-weight: 500;
              color: #303133;
              font-size: 12px;
            }
          }
          
          .result-message {
            font-size: 11px;
            color: #606266;
          }
        }
      }
    }
  }
  
  .upload-tips {
    .el-alert {
      ul {
        margin: 8px 0 0 0;
        padding-left: 20px;
        
        li {
          margin-bottom: 4px;
        }
      }
    }
  }
  
  .preview-content {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #e4e7ed;
    border-radius: 6px;
    padding: 16px;
    background: #fafafa;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 14px;
    line-height: 1.6;
    white-space: pre-wrap;
  }
}

[data-theme="dark"] .upload-page {
  .page-header {
    h2 {
      color: #e5eaf3;
    }
    
    p {
      color: #c0c4cc;
    }
  }
  
  .metadata-section {
    background: #2d2d2d;
    border-color: #434a50;
    
    h4 {
      color: #e5eaf3;
    }
  }
  
  .folder-upload-container {
    .upload-dragger {
      border-color: #434a50;
      background-color: #2d2d2d;
      
      .el-upload__text {
        color: #c0c4cc;
        
        em {
          color: #409eff;
        }
      }
      
      .el-upload__tip {
        color: #909399;
      }
      
      &:hover {
        border-color: #409eff;
        background-color: #363636;
      }
    }
  }
  
  .upload-tasks {
    .task-item {
      border-color: #434a50;
      background: #2d2d2d;
      
      &.task-completed {
        background: #1e3a4a;
        border-color: #2979ff;
      }
      
      &.task-error {
        background: #3a1e1e;
        border-color: #f44336;
      }
      
      .task-header .task-info .task-name {
        color: #e5eaf3;
      }
      
      .task-metadata .file-count {
        color: #909399;
      }
      
      .task-progress .progress-text {
        color: #c0c4cc;
      }
      
      .task-result {
        &.success {
          background: #1b5e20;
          color: #c8e6c9;
        }
        
        &.error {
          background: #b71c1c;
          color: #ffcdd2;
        }
      }
      
      .task-details .result-item {
        border-color: #434a50;
        background: #1d1e1f;
        
        .result-header .filename {
          color: #e5eaf3;
        }
        
        .result-message {
          color: #c0c4cc;
        }
      }
    }
  }
  
  .preview-content {
    border-color: #434a50;
    background: #2d2d2d;
    color: #e5eaf3;
  }
}
</style>
