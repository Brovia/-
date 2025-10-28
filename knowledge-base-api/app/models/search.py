"""
搜索相关数据模型
"""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class SearchType(str, Enum):
    """搜索类型枚举"""

    SEMANTIC = "semantic"


class SearchRequest(BaseModel):
    """搜索请求模型"""

    query: str = Field(..., min_length=1, max_length=1000, description="搜索查询")
    search_type: SearchType = Field(SearchType.SEMANTIC, description="搜索类型")
    limit: int = Field(10, ge=1, le=100, description="返回结果数量")
    offset: int = Field(0, ge=0, description="结果偏移量")
    source: Optional[str] = Field(None, description="指定文档来源")
    provider: Optional[str] = Field(None, description="指定云服务提供商")
    category: Optional[str] = Field(None, description="指定文档分类")
    min_score: float = Field(0.0, ge=0.0, le=1.0, description="最小相似度阈值")


class SearchResult(BaseModel):
    """单个搜索结果"""

    id: int
    title: str
    content: str
    source: str
    score: float
    metadata: Optional[dict[str, Any]] = None
    highlight: Optional[list[str]] = None


class SearchResponse(BaseModel):
    """搜索响应模型"""

    total: int
    results: list[SearchResult]
    query: str
    search_type: SearchType
    processing_time: float


class QuestionAnswerRequest(BaseModel):
    """问答请求模型"""

    question: str = Field(..., min_length=1, max_length=1000, description="问题")
    context_limit: int = Field(3, ge=1, le=10, description="上下文文档数量")
    include_sources: bool = Field(True, description="是否包含来源信息")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="回答随机性")
    provider: Optional[str] = Field(None, description="过滤特定云服务提供商")
    category: Optional[str] = Field(None, description="过滤特定产品分类")


class AnswerSource(BaseModel):
    """答案来源"""

    document: str
    excerpt: str
    relevance: float


class QuestionAnswerResponse(BaseModel):
    """问答响应模型"""

    answer: str
    confidence: float
    sources: list[AnswerSource]
    processing_time: float


class SummarizeRequest(BaseModel):
    """摘要请求模型"""

    document_id: Optional[int] = Field(None, description="文档ID")
    text: Optional[str] = Field(None, description="待摘要文本")
    summary_type: str = Field("brief", pattern="^(brief|detailed)$", description="摘要类型")
    max_length: int = Field(200, ge=50, le=1000, description="最大摘要长度")


class SummarizeResponse(BaseModel):
    """摘要响应模型"""

    summary: str
    original_length: int
    summary_length: int
    compression_ratio: float


class RecommendRequest(BaseModel):
    """推荐请求模型"""

    document_id: Optional[int] = Field(None, description="基准文档ID")
    query: Optional[str] = Field(None, description="查询文本")
    limit: int = Field(5, ge=1, le=20, description="推荐数量")
    similarity_threshold: float = Field(0.5, ge=0.0, le=1.0, description="相似度阈值")


class RecommendResponse(BaseModel):
    """推荐响应模型"""

    recommendations: list[SearchResult]
    base_document: Optional[str] = None
    processing_time: float
