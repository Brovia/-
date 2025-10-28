<template>
  <div class="directory-demo">
    <h3>云厂商目录结构演示</h3>
    <p>以下是按云厂商和产品分类组织的文档目录结构：</p>
    
    <div class="demo-tree">
      <el-tree
        :data="demoTree"
        :props="treeProps"
        :expand-on-click-node="false"
        node-key="id"
        :default-expanded-keys="['provider-腾讯云']"
        class="demo-tree-component"
      >
        <template #default="{ node, data }">
          <div class="demo-tree-node">
            <el-icon v-if="data.type === 'provider'" color="#006EFF">
              <Cloud />
            </el-icon>
            <el-icon v-else color="#606266">
              <Server />
            </el-icon>
            <span 
              :style="{ 
                color: data.type === 'provider' ? data.color : '#606266',
                fontWeight: data.type === 'provider' ? 'bold' : 'normal',
                marginLeft: '8px'
              }"
            >
              {{ data.name }}
            </span>
          </div>
        </template>
      </el-tree>
    </div>
    
    <div class="demo-features">
      <h4>功能特性：</h4>
      <ul>
        <li>✅ 按云厂商分类组织文档</li>
        <li>✅ 每个厂商下按产品分类</li>
        <li>✅ 树形目录结构展示</li>
        <li>✅ 点击目录查看对应文档</li>
        <li>✅ 支持搜索和过滤</li>
        <li>✅ 树形视图和列表视图切换</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Cloud, Server } from '@element-plus/icons-vue'
import { generateDirectoryTree } from '@/utils/directory-structure'

const demoTree = ref(generateDirectoryTree())
const treeProps = {
  children: 'children',
  label: 'name'
}
</script>

<style lang="scss" scoped>
.directory-demo {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  margin: 20px 0;
  
  h3 {
    color: #303133;
    margin-bottom: 10px;
  }
  
  p {
    color: #606266;
    margin-bottom: 20px;
  }
  
  .demo-tree {
    background: #fff;
    border: 1px solid #e4e7ed;
    border-radius: 6px;
    padding: 16px;
    margin-bottom: 20px;
    
    .demo-tree-component {
      :deep(.el-tree-node__content) {
        height: 36px;
        border-radius: 4px;
        margin-bottom: 2px;
        
        &:hover {
          background-color: #f5f7fa;
        }
      }
    }
  }
  
  .demo-features {
    h4 {
      color: #303133;
      margin-bottom: 10px;
    }
    
    ul {
      margin: 0;
      padding-left: 20px;
      
      li {
        color: #606266;
        margin-bottom: 5px;
      }
    }
  }
  
  .demo-tree-node {
    display: flex;
    align-items: center;
    width: 100%;
  }
}
</style>
