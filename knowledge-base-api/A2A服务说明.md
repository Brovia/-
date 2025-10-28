# 标准A2A协议使用指南

## 概述

知识库系统现符合标准A2A（Agent-to-Agent）协议规范，支持JSON-RPC 2.0格式的标准通信。

## A2A协议合规性

### 完全符合标准A2A协议

1. **JSON-RPC 2.0格式** - 使用标准JSON-RPC协议
2. **标准AgentCard** - 符合A2A协议的AgentCard格式
3. **统一消息格式** - 标准化的请求/响应格式
4. **标准错误处理** - 使用JSON-RPC标准错误代码
5. **服务发现** - 支持Agent能力发现
6. **认证机制** - 预留认证接口

### 协议特点

- **互操作性**: 与其他A2A兼容的Agent无缝协作
- **标准化**: 遵循Google Cloud A2A协议规范
- **扩展性**: 支持未来协议版本升级
- **兼容性**: 同时支持标准协议和兼容模式


## 配置说明

A2A服务的搜索参数可以直接在`app/core/config.py`文件中配置，用于控制知识库检索的最小相似度和返回给agent的文本数量。

### 配置位置

在`app/core/config.py`文件的`Settings`类中，找到以下配置项：

```python
# A2A搜索配置
# 默认返回结果数量 (1-50)
A2A_DEFAULT_LIMIT: int = 5

# 默认最小相似度阈值 (0.0-1.0)
# 0.0: 返回所有结果
# 0.1-0.3: 宽松过滤，适合全面搜索
# 0.3-0.5: 中等过滤，平衡质量和数量
# 0.5-0.7: 严格过滤，高质量结果
# 0.7-1.0: 极严格过滤，只返回最相关结果
A2A_DEFAULT_MIN_SCORE: float = 0.3

# 最大返回结果数量限制
A2A_MAX_LIMIT: int = 50

# 最大查询长度限制
A2A_MAX_QUERY_LENGTH: int = 500
```

## API端点

### 1. 标准A2A协议接口

**POST** `/a2a/protocol`

使用标准JSON-RPC 2.0格式的A2A协议接口。

**请求格式**:
```json
{
    "jsonrpc": "2.0",
    "id": "请求ID",
    "method": "方法名",
    "params": {
        "参数": "值"
    }
}
```

**支持的方法**:

#### get_agent_card
获取Agent能力信息
```json
{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "get_agent_card"
}
```

#### search_knowledge
知识库检索
```json
{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "search_knowledge",
    "params": {
        "query": "搜索查询",
        "limit": 5,
        "provider": "腾讯云",
        "category": "负载均衡",
        "min_score": 0.3
    }
}
```

#### health_check
健康检查
```json
{
    "jsonrpc": "2.0",
    "id": "3",
    "method": "health_check"
}
```

### 2. 兼容模式接口

**POST** `/a2a`

保持向后兼容的统一接口。

**GET** `/a2a/`

直接获取Agent卡片。

**POST** `/a2a/search`

直接进行知识库检索。

## AgentCard格式

标准A2A协议AgentCard包含以下字段：

```json
{
    "name": "云产品文档知识库",
    "version": "1.0.0",
    "description": "专业的云产品知识库检索服务",
    "capabilities": [
        "语义搜索",
        "文档检索",
        "竞品分析",
        "技术对比",
        "多厂商支持"
    ],
    "endpoints": {
        "get_agent_card": {
            "method": "GET",
            "path": "/a2a/",
            "description": "获取Agent能力信息"
        },
        "search_knowledge": {
            "method": "POST",
            "path": "/a2a/search",
            "description": "知识库检索"
        },
        "a2a_protocol": {
            "method": "POST",
            "path": "/a2a/protocol",
            "description": "标准A2A协议接口"
        }
    },
    "authentication": {
        "type": "none",
        "description": "当前无需认证"
    },
    "metadata": {
        "protocol_version": "1.0",
        "supported_formats": ["json"],
        "max_request_size": "1MB"
    },
    "supported_providers": [
        "腾讯云", "阿里云", "火山云", "华为云", "AWS", "Azure", "GCP"
    ],
    "supported_categories": [
        "负载均衡", "私有网络", "弹性IP", "NAT网关", "专线", "云联网", "VPN"
    ],
    "skills": [
        "负载均衡技术分析",
        "云网络产品对比",
        "NAT网关功能分析",
        "弹性IP服务对比",
        "专线服务分析",
        "云联网技术对比",
        "VPN产品分析"
    ]
}
```

## 错误处理

### 标准JSON-RPC错误代码

- **-32600**: Invalid Request - 无效请求
- **-32601**: Method not found - 方法未找到
- **-32602**: Invalid params - 无效参数
- **-32603**: Internal error - 内部错误

### 错误响应格式

```json
{
    "jsonrpc": "2.0",
    "id": "请求ID",
    "method": "方法名",
    "error": {
        "code": -32602,
        "message": "Invalid params: missing required field 'query'",
        "data": {
            "required_fields": ["query"]
        }
    }
}
```

## 集成示例

### Python标准A2A客户端

```python
import requests
import json

class A2AClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.protocol_url = f"{base_url}/a2a/protocol"
    
    def _make_request(self, method, params=None, request_id="1"):
        """发送标准A2A请求"""
        request_data = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method
        }
        if params:
            request_data["params"] = params
        
        response = requests.post(self.protocol_url, json=request_data)
        return response.json()
    
    def get_agent_card(self):
        """获取Agent卡片"""
        return self._make_request("get_agent_card")
    
    def search_knowledge(self, query, **kwargs):
        """搜索知识库"""
        params = {"query": query}
        params.update(kwargs)
        return self._make_request("search_knowledge", params)
    
    def health_check(self):
        """健康检查"""
        return self._make_request("health_check")

# 使用示例
client = A2AClient("http://your-domain:8000")

# 获取Agent信息
agent_info = client.get_agent_card()
print(f"Agent: {agent_info['result']['agent_card']['name']}")

# 搜索知识库
results = client.search_knowledge(
    query="负载均衡对比",
    provider="腾讯云",
    limit=5
)
print(f"找到 {results['result']['total_results']} 个结果")

# 健康检查
health = client.health_check()
print(f"服务状态: {health['result']['status']}")
```

### JavaScript标准A2A客户端

```javascript
class A2AClient {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
        this.protocolUrl = `${baseUrl}/a2a/protocol`;
    }
    
    async makeRequest(method, params = null, requestId = "1") {
        const requestData = {
            jsonrpc: "2.0",
            id: requestId,
            method: method
        };
        
        if (params) {
            requestData.params = params;
        }
        
        const response = await fetch(this.protocolUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        return await response.json();
    }
    
    async getAgentCard() {
        return await this.makeRequest("get_agent_card");
    }
    
    async searchKnowledge(query, options = {}) {
        const params = { query, ...options };
        return await this.makeRequest("search_knowledge", params);
    }
    
    async healthCheck() {
        return await this.makeRequest("health_check");
    }
}

// 使用示例
const client = new A2AClient("http://your-domain:8000");

(async () => {
    try {
        // 获取Agent信息
        const agentInfo = await client.getAgentCard();
        console.log(`Agent: ${agentInfo.result.agent_card.name}`);
        
        // 搜索知识库
        const results = await client.searchKnowledge("负载均衡对比", {
            provider: "腾讯云",
            limit: 5
        });
        console.log(`找到 ${results.result.total_results} 个结果`);
        
        // 健康检查
        const health = await client.healthCheck();
        console.log(`服务状态: ${health.result.status}`);
        
    } catch (error) {
        console.error('请求失败:', error);
    }
})();
```

## 部署和配置

### 启动服务

```bash
cd /root/jpfx/knowledge-base-api
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 验证部署

```bash
# 测试标准A2A协议
python3 scripts/test_standard_a2a.py
