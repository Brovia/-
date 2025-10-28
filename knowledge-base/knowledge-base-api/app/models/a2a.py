"""
A2A (Agent-to-Agent) 数据模型 - 符合标准A2A协议
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum


class A2AMessageType(str, Enum):
    """A2A消息类型"""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class A2AMethod(str, Enum):
    """A2A方法类型"""
    GET_AGENT_CARD = "get_agent_card"
    SEARCH_KNOWLEDGE = "search_knowledge"
    HEALTH_CHECK = "health_check"


class AgentCard(BaseModel):
    """标准A2A AgentCard格式"""
    
    # 必需字段
    name: str = Field(..., description="Agent名称")
    version: str = Field(..., description="版本号")
    description: str = Field(..., description="Agent描述")
    
    # A2A协议标准字段
    capabilities: List[str] = Field(..., description="能力列表")
    endpoints: Dict[str, Dict[str, Any]] = Field(..., description="端点信息")
    authentication: Optional[Dict[str, Any]] = Field(None, description="认证信息")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    
    # 业务特定字段
    supported_providers: List[str] = Field(..., description="支持的云服务提供商")
    supported_categories: List[str] = Field(..., description="支持的产品分类")
    skills: List[str] = Field(..., description="技能列表")


class A2AMessage(BaseModel):
    """标准A2A消息格式"""
    
    # 必需字段
    jsonrpc: str = Field("2.0", description="JSON-RPC版本")
    id: Optional[Union[str, int]] = Field(None, description="请求ID")
    method: str = Field(..., description="方法名")
    
    # 可选字段
    params: Optional[Dict[str, Any]] = Field(None, description="参数")
    result: Optional[Any] = Field(None, description="结果")
    error: Optional[Dict[str, Any]] = Field(None, description="错误信息")


class A2AError(BaseModel):
    """A2A错误格式"""
    
    code: int = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    data: Optional[Any] = Field(None, description="错误数据")


class KnowledgeSearchRequest(BaseModel):
    """知识检索请求"""
    
    query: str = Field(..., description="搜索查询", min_length=1, max_length=500)
    limit: int = Field(None, description="返回结果数量", ge=1, le=50)
    provider: Optional[str] = Field(None, description="云服务提供商过滤")
    category: Optional[str] = Field(None, description="产品分类过滤")
    min_score: float = Field(None, description="最小相似度阈值", ge=0.0, le=1.0)


class KnowledgeSearchResponse(BaseModel):
    """知识检索响应"""
    
    success: bool = Field(..., description="请求是否成功")
    query: str = Field(..., description="原始查询")
    total_results: int = Field(..., description="总结果数")
    results: List[Dict[str, Any]] = Field(..., description="搜索结果")
    processing_time: float = Field(..., description="处理时间(秒)")
    error_message: Optional[str] = Field(None, description="错误信息")


# 兼容性保持的旧模型
class A2ARequest(BaseModel):
    """A2A统一请求 - 兼容旧版本"""
    
    action: str = Field(..., description="请求动作", pattern="^(agent_card|knowledge_search)$")
    data: Dict[str, Any] = Field(..., description="请求数据")


class A2AResponse(BaseModel):
    """A2A统一响应 - 兼容旧版本"""
    
    success: bool = Field(..., description="请求是否成功")
    action: str = Field(..., description="响应动作")
    data: Dict[str, Any] = Field(..., description="响应数据")
    error_message: Optional[str] = Field(None, description="错误信息")
    timestamp: float = Field(..., description="响应时间戳")
