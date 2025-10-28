<template>
  <div class="qa-page">
    <div class="page-header">
      <h2>竞品分析Agent</h2>
      <p>基于知识库的云计算产品竞品分析系统</p>
    </div>

    <el-row :gutter="20">
      <!-- 问答区域 -->
      <el-col :span="16">
        <div class="card">
          <h3>竞品分析对话</h3>
          
          <!-- 对话历史 -->
          <div class="chat-container">
            <div 
              v-for="(message, index) in chatHistory" 
              :key="index"
              class="message-item"
              :class="{ 'user-message': message.type === 'user', 'ai-message': message.type === 'ai' }"
            >
              <div class="message-avatar">
                <el-icon v-if="message.type === 'user'"><User /></el-icon>
                <el-icon v-else><ChatDotRound /></el-icon>
              </div>
              
              <div class="message-content">
                <div class="message-text">{{ message.content }}</div>
                
                <!-- AI回答的额外信息 -->
                <div v-if="message.type === 'ai' && message.metadata" class="message-meta">
                  <div class="confidence">
                    <span>置信度: {{ (message.metadata.confidence * 100).toFixed(1) }}%</span>
                    <span>处理时间: {{ message.metadata.processing_time }}s</span>
                  </div>
                  
                  <!-- 来源信息 -->
                  <div v-if="message.metadata.sources && message.metadata.sources.length > 0" class="sources">
                    <div class="sources-title">参考来源:</div>
                    <div 
                      v-for="(source, idx) in message.metadata.sources" 
                      :key="idx"
                      class="source-item"
                    >
                      <div class="source-document">{{ source.document }}</div>
                      <div class="source-excerpt">{{ source.excerpt }}</div>
                      <div class="source-relevance">相关性: {{ (source.relevance * 100).toFixed(1) }}%</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 加载状态 -->
            <div v-if="answering" class="message-item ai-message">
              <div class="message-avatar">
                <el-icon><Robot /></el-icon>
              </div>
              <div class="message-content">
                <div class="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 输入区域 -->
          <div class="input-area">
            <el-form @submit.prevent="askQuestion">
              <el-row :gutter="10">
                <el-col :span="18">
                  <el-input
                    v-model="questionInput"
                    placeholder="请输入竞品分析问题，如：腾讯云CLB和阿里云ALB有什么区别？"
                    @keyup.enter="askQuestion"
                    :disabled="answering"
                    type="textarea"
                    :rows="2"
                    resize="none"
                  />
                </el-col>
                <el-col :span="6">
                  <el-button 
                    type="primary" 
                    @click="askQuestion"
                    :loading="answering"
                    :disabled="!questionInput.trim()"
                    style="width: 100%; height: 100%;"
                  >
                    分析
                  </el-button>
                </el-col>
              </el-row>
            </el-form>
          </div>
        </div>
      </el-col>
      
      <!-- 侧边栏 -->
      <el-col :span="8">
        <!-- 竞品分析设置 -->
        <div class="card">
          <h3>分析设置</h3>
          
          <el-form :model="qaSettings" label-width="80px">
            <el-form-item label="上下文数量">
              <el-slider
                v-model="qaSettings.context_limit"
                :min="1"
                :max="10"
                :step="1"
                show-input
                :show-input-controls="false"
              />
            </el-form-item>
            
            <el-form-item label="回答随机性">
              <el-slider
                v-model="qaSettings.temperature"
                :min="0"
                :max="2"
                :step="0.1"
                show-input
                :show-input-controls="false"
              />
            </el-form-item>
            
            <el-form-item label="显示来源">
              <el-switch v-model="qaSettings.include_sources" />
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 竞品分析示例 -->
        <div class="card">
          <h3>分析示例</h3>
          
          <div class="quick-questions">
            <el-button 
              v-for="(question, index) in quickQuestions" 
              :key="index"
              size="small"
              @click="selectQuickQuestion(question)"
              :disabled="answering"
            >
              {{ question }}
            </el-button>
          </div>
        </div>
        
        <!-- 分析统计 -->
        <div class="card">
          <h3>分析统计</h3>
          
          <div class="qa-stats">
            <div class="stat-item">
              <span class="stat-label">总提问数:</span>
              <span class="stat-value">{{ chatHistory.filter(m => m.type === 'user').length }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">平均置信度:</span>
              <span class="stat-value">{{ averageConfidence }}%</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">平均响应时间:</span>
              <span class="stat-value">{{ averageResponseTime }}s</span>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { User, ChatDotRound } from '@element-plus/icons-vue'
import { knowledgeService } from '@/services/api'


// 响应式数据
const questionInput = ref('')
const answering = ref(false)
const chatHistory = ref([])

// 问答设置
const qaSettings = reactive({
  context_limit: 3,
  temperature: 0.7,
  include_sources: true
})

// 竞品分析示例
const quickQuestions = [
  '腾讯云CLB和阿里云ALB有什么区别？',
  'AWS ELB和Azure Load Balancer对比分析',
  '华为云ELB和火山云CLB功能对比',
  '各厂商负载均衡产品优劣势分析',
  '云厂商私有网络产品对比',
  '弹性IP服务竞品分析',
  'NAT网关产品功能对比'
]

// 计算属性
const averageConfidence = computed(() => {
  const aiMessages = chatHistory.value.filter(m => m.type === 'ai' && m.metadata?.confidence)
  if (aiMessages.length === 0) return 0
  
  const totalConfidence = aiMessages.reduce((sum, msg) => sum + msg.metadata.confidence, 0)
  return ((totalConfidence / aiMessages.length) * 100).toFixed(1)
})

const averageResponseTime = computed(() => {
  const aiMessages = chatHistory.value.filter(m => m.type === 'ai' && m.metadata?.processing_time)
  if (aiMessages.length === 0) return 0
  
  const totalTime = aiMessages.reduce((sum, msg) => sum + msg.metadata.processing_time, 0)
  return (totalTime / aiMessages.length).toFixed(2)
})

// 提问
const askQuestion = async () => {
  if (!questionInput.value.trim()) {
    ElMessage.warning('请输入问题')
    return
  }
  
  const question = questionInput.value.trim()
  
  try {
    // 添加用户消息到历史
    chatHistory.value.push({
      type: 'user',
      content: question,
      timestamp: new Date()
    })
    
    // 清空输入框
    questionInput.value = ''
    answering.value = true
    
    // 发送问答请求
    const response = await knowledgeService.askQuestion({
      question: question,
      context_limit: qaSettings.context_limit,
      include_sources: qaSettings.include_sources,
      temperature: qaSettings.temperature
    })
    
    // 添加AI回答到历史
    chatHistory.value.push({
      type: 'ai',
      content: response.data.answer,
      metadata: {
        confidence: response.data.confidence,
        processing_time: response.data.processing_time,
        sources: response.data.sources
      },
      timestamp: new Date()
    })
    
  } catch (error) {
    ElMessage.error('问答失败，请稍后重试')
    console.error('QA error:', error)
    
    // 添加错误消息
    chatHistory.value.push({
      type: 'ai',
      content: '抱歉，我暂时无法回答您的问题，请稍后重试。',
      metadata: {
        confidence: 0,
        processing_time: 0,
        sources: []
      },
      timestamp: new Date()
    })
  } finally {
    answering.value = false
  }
}

// 选择分析示例
const selectQuickQuestion = (question) => {
  questionInput.value = question
}

// 清空对话历史
const clearHistory = () => {
  chatHistory.value = []
  ElMessage.success('对话历史已清空')
}

// 组件挂载
onMounted(() => {
  // 添加欢迎消息
  chatHistory.value.push({
    type: 'ai',
    content: '您好！我是云计算产品竞品分析专家，专门帮助您分析腾讯云、阿里云、火山云、华为云、AWS、Azure、GCP等云厂商的产品优劣势。我可以进行负载均衡、私有网络、弹性IP、NAT网关、专线、云联网、VPN等产品的深度竞品对比分析。请告诉我您想了解哪些产品的对比分析！',
    metadata: {
      confidence: 1.0,
      processing_time: 0,
      sources: []
    },
    timestamp: new Date()
  })
})
</script>

<style lang="scss" scoped>
.qa-page {
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
  
  .chat-container {
    height: 500px;
    overflow-y: auto;
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
    background: #fafafa;
    
    .message-item {
      display: flex;
      margin-bottom: 16px;
      
      &.user-message {
        flex-direction: row-reverse;
        
        .message-content {
          background: #409eff;
          color: white;
          margin-right: 12px;
          margin-left: 0;
        }
      }
      
      &.ai-message {
        .message-content {
          background: white;
          color: #303133;
          margin-left: 12px;
        }
      }
      
      .message-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: #f0f0f0;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        
        .el-icon {
          font-size: 16px;
          color: #666;
        }
      }
      
      .message-content {
        max-width: 70%;
        padding: 12px 16px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        
        .message-text {
          line-height: 1.6;
          word-wrap: break-word;
        }
        
        .message-meta {
          margin-top: 12px;
          padding-top: 12px;
          border-top: 1px solid rgba(0, 0, 0, 0.1);
          
          .confidence {
            font-size: 12px;
            color: #666;
            margin-bottom: 8px;
            
            span {
              margin-right: 16px;
            }
          }
          
          .sources {
            .sources-title {
              font-size: 12px;
              font-weight: bold;
              color: #666;
              margin-bottom: 8px;
            }
            
            .source-item {
              background: rgba(0, 0, 0, 0.05);
              border-radius: 6px;
              padding: 8px;
              margin-bottom: 6px;
              
              .source-document {
                font-weight: bold;
                font-size: 12px;
                margin-bottom: 4px;
              }
              
              .source-excerpt {
                font-size: 11px;
                color: #666;
                line-height: 1.4;
                margin-bottom: 4px;
              }
              
              .source-relevance {
                font-size: 10px;
                color: #999;
              }
            }
          }
        }
      }
    }
    
    .typing-indicator {
      display: flex;
      align-items: center;
      
      span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #409eff;
        margin-right: 4px;
        animation: typing 1.4s infinite ease-in-out;
        
        &:nth-child(1) { animation-delay: -0.32s; }
        &:nth-child(2) { animation-delay: -0.16s; }
        &:nth-child(3) { animation-delay: 0s; }
      }
    }
  }
  
  .input-area {
    .el-textarea {
      .el-textarea__inner {
        border-radius: 8px;
      }
    }
  }
  
  .quick-questions {
    display: flex;
    flex-direction: column;
    gap: 8px;
    
    .el-button {
      text-align: left;
      justify-content: flex-start;
      white-space: normal;
      height: auto;
      padding: 8px 12px;
      line-height: 1.4;
    }
  }
  
  .qa-stats {
    .stat-item {
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      
      .stat-label {
        color: #666;
        font-size: 14px;
      }
      
      .stat-value {
        font-weight: bold;
        color: #409eff;
      }
    }
  }
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

[data-theme="dark"] .qa-page {
  .page-header {
    h2 {
      color: #e5eaf3;
    }
    
    p {
      color: #c0c4cc;
    }
  }
  
  .chat-container {
    background: #2d2d2d;
    border-color: #434a50;
    
    .message-item {
      &.ai-message .message-content {
        background: #1d1e1f;
        color: #e5eaf3;
        
        .message-meta {
          border-top-color: #434a50;
          
          .confidence {
            color: #c0c4cc;
          }
          
          .sources {
            .sources-title {
              color: #c0c4cc;
            }
            
            .source-item {
              background: rgba(255, 255, 255, 0.05);
              
              .source-document {
                color: #e5eaf3;
              }
              
              .source-excerpt {
                color: #c0c4cc;
              }
              
              .source-relevance {
                color: #909399;
              }
            }
          }
        }
      }
    }
  }
  
  .qa-stats {
    .stat-item {
      .stat-label {
        color: #c0c4cc;
      }
    }
  }
}
</style>
