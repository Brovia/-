"""
A2A (Agent-to-Agent) 服务
"""

import time
import logging
from typing import Any, Dict, List, Optional

from app.core.config import get_settings
from app.models.a2a import (
    AgentCard,
    A2AMessage,
    A2AError,
    A2AMethod,
    A2ARequest,
    A2AResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.services.search_engine import SearchEngine

logger = logging.getLogger(__name__)
settings = get_settings()


class A2AService:
    """A2A服务类"""
    
    def __init__(self):
        self.search_engine = SearchEngine()
        self.agent_card = self._create_agent_card()
    
    def _create_agent_card(self) -> AgentCard:
        """创建标准A2A AgentCard"""
        return AgentCard(
            name="云产品文档知识库",
            version=settings.APP_VERSION,
            description="专业的云产品知识库检索服务",
            capabilities=[
                "语义搜索",
                "文档检索", 
                "竞品分析",
                "技术对比",
                "多厂商支持"
            ],
            endpoints={
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
                    "path": "/a2a",
                    "description": "标准A2A协议接口"
                }
            },
            authentication={
                "type": "none",
                "description": "当前无需认证"
            },
            metadata={
                "protocol_version": "1.0",
                "supported_formats": ["json"],
                "max_request_size": "1MB"
            },
            skills=[
                "负载均衡技术分析",
                "云网络产品对比",
                "NAT网关功能分析",
                "弹性IP服务对比",
                "专线服务分析",
                "云联网技术对比",
                "VPN产品分析"
            ],
            supported_providers=[
                "腾讯云",
                "阿里云", 
                "火山云",
                "华为云",
                "AWS",
                "Azure",
                "GCP"
            ],
            supported_categories=[
                "负载均衡",
                "私有网络",
                "弹性IP",
                "NAT网关",
                "专线",
                "云联网",
                "VPN"
            ]
        )
    
    def get_agent_card(self) -> Dict[str, Any]:
        """获取Agent能力卡片"""
        try:
            return {
                "success": True,
                "agent_card": self.agent_card.dict(),
                "timestamp": time.time()
            }
        except Exception as e:
            logger.error(f"Failed to get agent card: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }
    
    def search_knowledge(self, request: KnowledgeSearchRequest) -> Dict[str, Any]:
        """知识库检索"""
        try:
            start_time = time.time()
            
            # 使用配置中的默认值，如果请求中没有指定的话
            effective_limit = request.limit if request.limit is not None else settings.A2A_DEFAULT_LIMIT
            effective_min_score = request.min_score if request.min_score is not None else settings.A2A_DEFAULT_MIN_SCORE
            
            # 应用限制
            effective_limit = min(effective_limit, settings.A2A_MAX_LIMIT)
            effective_min_score = max(0.0, min(1.0, effective_min_score))
            
            # 构建过滤条件
            filters = {}
            if request.provider:
                filters['provider'] = request.provider
            if request.category:
                filters['category'] = request.category
            
            # 执行搜索
            search_results = self.search_engine.search(
                query=request.query,
                limit=effective_limit,
                filters=filters if filters else None,
            )
            
            # 过滤低分结果
            filtered_results = []
            for result in search_results['results']:
                if result['score'] >= effective_min_score:
                    filtered_results.append(result)
            
            processing_time = time.time() - start_time
            
            return {
                "success": True,
                "query": request.query,
                "total_results": len(filtered_results),
                "results": filtered_results,
                "processing_time": round(processing_time, 3),
                "search_params": {
                    "limit": effective_limit,
                    "min_score": effective_min_score,
                    "provider": request.provider,
                    "category": request.category
                },
                "timestamp": time.time()
            }
            
        except Exception as e:
            logger.error(f"Knowledge search failed: {str(e)}")
            return {
                "success": False,
                "query": request.query,
                "total_results": 0,
                "results": [],
                "processing_time": 0,
                "error_message": str(e),
                "timestamp": time.time()
            }
    
    def handle_request(self, request: A2ARequest) -> A2AResponse:
        """处理A2A请求"""
        try:
            if request.action == "agent_card":
                result = self.get_agent_card()
                return A2AResponse(
                    success=result["success"],
                    action="agent_card",
                    data=result,
                    error_message=result.get("error"),
                    timestamp=time.time()
                )
            
            elif request.action == "knowledge_search":
                # 验证请求数据
                if "query" not in request.data:
                    return A2AResponse(
                        success=False,
                        action="knowledge_search",
                        data={},
                        error_message="Missing required field: query",
                        timestamp=time.time()
                    )
                
                # 创建搜索请求
                search_request = KnowledgeSearchRequest(**request.data)
                result = self.search_knowledge(search_request)
                
                return A2AResponse(
                    success=result["success"],
                    action="knowledge_search",
                    data=result,
                    error_message=result.get("error_message"),
                    timestamp=time.time()
                )
            
            else:
                return A2AResponse(
                    success=False,
                    action=request.action,
                    data={},
                    error_message=f"Unsupported action: {request.action}",
                    timestamp=time.time()
                )
                
        except Exception as e:
            logger.error(f"A2A request handling failed: {str(e)}")
            return A2AResponse(
                success=False,
                action=request.action,
                data={},
                error_message=str(e),
                timestamp=time.time()
            )
    
    def handle_a2a_message(self, message: A2AMessage) -> A2AMessage:
        """处理标准A2A协议消息"""
        try:
            if message.method == A2AMethod.GET_AGENT_CARD:
                result = self.get_agent_card()
                return A2AMessage(
                    jsonrpc="2.0",
                    id=message.id,
                    method=message.method,
                    result=result
                )
            
            elif message.method == A2AMethod.SEARCH_KNOWLEDGE:
                if not message.params or "query" not in message.params:
                    error = A2AError(
                        code=-32602,
                        message="Invalid params: missing required field 'query'",
                        data={"required_fields": ["query"]}
                    )
                    return A2AMessage(
                        jsonrpc="2.0",
                        id=message.id,
                        method=message.method,
                        error=error.dict()
                    )
                
                # 创建搜索请求
                search_request = KnowledgeSearchRequest(**message.params)
                result = self.search_knowledge(search_request)
                
                return A2AMessage(
                    jsonrpc="2.0",
                    id=message.id,
                    method=message.method,
                    result=result
                )
            
            elif message.method == A2AMethod.HEALTH_CHECK:
                health_result = {
                    "status": "healthy",
                    "agent_card_available": True,
                    "search_available": True,
                    "timestamp": time.time()
                }
                return A2AMessage(
                    jsonrpc="2.0",
                    id=message.id,
                    method=message.method,
                    result=health_result
                )
            
            else:
                error = A2AError(
                    code=-32601,
                    message=f"Method not found: {message.method}",
                    data={"available_methods": [method.value for method in A2AMethod]}
                )
                return A2AMessage(
                    jsonrpc="2.0",
                    id=message.id,
                    method=message.method,
                    error=error.dict()
                )
                
        except Exception as e:
            logger.error(f"A2A message handling failed: {str(e)}")
            error = A2AError(
                code=-32603,
                message="Internal error",
                data={"error": str(e)}
            )
            return A2AMessage(
                jsonrpc="2.0",
                id=message.id,
                method=message.method,
                error=error.dict()
            )
