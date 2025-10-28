"""
A2A (Agent-to-Agent) API端点
"""

import logging
import time
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.models.a2a import A2ARequest, A2AResponse, A2AMessage, KnowledgeSearchRequest
from app.services.a2a_service import A2AService

router = APIRouter()
logger = logging.getLogger(__name__)

# 初始化A2A服务
a2a_service = A2AService()


@router.get("/", summary="获取Agent能力卡片")
async def get_agent_card() -> Dict[str, Any]:
    """
    获取Agent能力卡片信息
    
    返回Agent的名称、版本、能力、技能等详细信息，供其他Agent了解本服务的功能
    """
    try:
        result = a2a_service.get_agent_card()
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Failed to get agent card")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent card: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent card: {str(e)}"
        )


@router.post("/protocol", summary="标准A2A协议接口")
async def a2a_protocol_endpoint(message: A2AMessage) -> A2AMessage:
    """
    标准A2A协议接口，使用JSON-RPC 2.0格式
    
    支持的方法:
    - **get_agent_card**: 获取Agent能力信息
    - **search_knowledge**: 知识库检索
    - **health_check**: 健康检查
    
    请求示例:
    ```json
    {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "search_knowledge",
        "params": {
            "query": "负载均衡对比",
            "limit": 5,
            "provider": "腾讯云"
        }
    }
    ```
    """
    try:
        response = a2a_service.handle_a2a_message(message)
        return response
        
    except Exception as e:
        logger.error(f"A2A protocol request failed: {str(e)}")
        error_response = A2AMessage(
            jsonrpc="2.0",
            id=message.id,
            method=message.method,
            error={
                "code": -32603,
                "message": "Internal error",
                "data": {"error": str(e)}
            }
        )
        return error_response


@router.post("/", summary="A2A统一接口（兼容模式）")
async def a2a_endpoint(request: A2ARequest) -> A2AResponse:
    """
    A2A统一接口，支持多种操作
    
    支持的action:
    - **agent_card**: 获取Agent能力信息
    - **knowledge_search**: 知识库检索
    
    请求示例:
    ```json
    {
        "action": "knowledge_search",
        "data": {
            "query": "负载均衡对比",
            "limit": 5,
            "provider": "腾讯云",
            "category": "负载均衡"
        }
    }
    ```
    """
    try:
        response = a2a_service.handle_request(request)
        
        # 如果请求失败，返回HTTP错误状态
        if not response.success:
            if request.action == "agent_card":
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=response.error_message
                )
            elif request.action == "knowledge_search":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=response.error_message
                )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"A2A request failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"A2A request failed: {str(e)}"
        )


@router.post("/search", summary="知识库检索")
async def search_knowledge(request: KnowledgeSearchRequest) -> Dict[str, Any]:
    """
    直接的知识库检索接口
    
    提供语义搜索功能，支持按云服务提供商和产品分类过滤
    
    - **query**: 搜索查询文本
    - **limit**: 返回结果数量 (1-50)
    - **provider**: 云服务提供商过滤 (腾讯云、阿里云、火山云、华为云、AWS、Azure、GCP)
    - **category**: 产品分类过滤 (负载均衡、私有网络、弹性IP、NAT网关、专线、云联网、VPN)
    - **min_score**: 最小相似度阈值 (0.0-1.0)
    """
    try:
        result = a2a_service.search_knowledge(request)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error_message", "Search failed")
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Knowledge search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Knowledge search failed: {str(e)}"
        )


@router.get("/config", summary="获取A2A配置信息")
async def get_a2a_config() -> Dict[str, Any]:
    """
    获取A2A服务的配置信息
    
    返回当前的最小相似度阈值、默认返回数量等配置参数
    """
    try:
        from app.core.config import get_settings
        settings = get_settings()
        
        return {
            "success": True,
            "config": {
                "default_limit": settings.A2A_DEFAULT_LIMIT,
                "default_min_score": settings.A2A_DEFAULT_MIN_SCORE,
                "max_limit": settings.A2A_MAX_LIMIT,
                "max_query_length": settings.A2A_MAX_QUERY_LENGTH
            },
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get A2A config: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get config: {str(e)}"
        )


@router.get("/health", summary="A2A服务健康检查")
async def a2a_health_check() -> Dict[str, Any]:
    """
    A2A服务健康检查
    
    检查A2A服务的运行状态
    """
    try:
        # 测试Agent卡片获取
        agent_card_result = a2a_service.get_agent_card()
        
        # 测试搜索功能
        test_search = KnowledgeSearchRequest(query="测试", limit=1)
        search_result = a2a_service.search_knowledge(test_search)
        
        return {
            "status": "healthy",
            "agent_card_available": agent_card_result["success"],
            "search_available": search_result["success"],
            "timestamp": search_result["timestamp"]
        }
        
    except Exception as e:
        logger.error(f"A2A health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }
