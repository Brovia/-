"""
知识库API端点
"""

import time
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.search import (
    QuestionAnswerRequest,
    QuestionAnswerResponse,
    RecommendResponse,
    SearchResponse,
    SearchType,
    SummarizeRequest,
    SummarizeResponse,
)
from app.services.qa_service import QAService
from app.services.search_engine import SearchEngine
from app.services.vector_store import VectorStore

router = APIRouter()

# 初始化服务
search_engine = SearchEngine()
qa_service = QAService()

# 懒加载vector_store，避免模块加载时的集合ID缓存问题
def get_vector_store():
    return VectorStore()


@router.get("/search", response_model=SearchResponse, summary="搜索知识库")
async def search_knowledge(
    query: str = Query(..., description="搜索查询"),
    limit: int = Query(10, ge=1, le=100, description="返回结果数量"),
    offset: int = Query(0, ge=0, description="结果偏移量"),
    source: Optional[str] = Query(None, description="指定文档来源"),
    provider: Optional[str] = Query(None, description="指定云服务提供商"),
    category: Optional[str] = Query(None, description="指定文档分类"),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="最小相似度阈值"),
) -> SearchResponse:
    """
    搜索知识库文档（语义搜索）

    - **query**: 搜索查询文本
    - **limit**: 返回结果数量
    - **offset**: 结果偏移量
    - **source**: 过滤特定文档来源
    - **provider**: 过滤特定云服务提供商 (腾讯云、阿里云、火山云、华为云、AWS、Azure、GCP)
    - **category**: 过滤特定产品分类 (负载均衡、私有网络、弹性IP、NAT网关、专线、云联网、VPN)
    - **min_score**: 最小相似度阈值
    """
    try:
        # 构建过滤条件
        filters = {}
        if source:
            filters['filename'] = source
        if provider:
            filters['provider'] = provider
        if category:
            filters['category'] = category

        # 执行搜索
        search_results = search_engine.search(
            query=query,
            limit=limit + offset,  # 获取更多结果以支持偏移
            filters=filters if filters else None,
        )

        # 应用偏移和分数过滤
        filtered_results = []
        for result in search_results['results']:
            if result['score'] >= min_score:
                filtered_results.append(result)

        # 应用偏移
        paginated_results = filtered_results[offset : offset + limit]

        return SearchResponse(
            total=len(filtered_results),
            results=paginated_results,
            query=query,
            search_type=SearchType.SEMANTIC,
            processing_time=search_results['processing_time'],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Search failed: {str(e)}"
        )


@router.post("/qa", response_model=QuestionAnswerResponse, summary="问答服务")
async def ask_question(request: QuestionAnswerRequest) -> QuestionAnswerResponse:
    """
    基于知识库回答问题

    - **question**: 用户问题
    - **context_limit**: 上下文文档数量限制
    - **include_sources**: 是否包含来源信息
    - **temperature**: 回答的随机性程度
    - **provider**: 过滤特定云服务提供商 (腾讯云、阿里云、火山云、华为云、AWS、Azure、GCP)
    - **category**: 过滤特定产品分类 (负载均衡、私有网络、弹性IP、NAT网关、专线、云联网、VPN)
    """
    try:
        result = qa_service.answer_question(
            question=request.question,
            context_limit=request.context_limit,
            include_sources=request.include_sources,
            temperature=request.temperature,
            provider=request.provider,
            category=request.category,
        )

        return QuestionAnswerResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Question answering failed: {str(e)}",
        )


@router.post("/summarize", response_model=SummarizeResponse, summary="文本摘要")
async def summarize_content(
    request: SummarizeRequest, db: Session = Depends(get_db)
) -> SummarizeResponse:
    """
    生成文本摘要

    - **document_id**: 文档ID（与text二选一）
    - **text**: 待摘要文本（与document_id二选一）
    - **summary_type**: 摘要类型 (brief/detailed)
    - **max_length**: 最大摘要长度
    """
    try:
        text_to_summarize = ""

        if request.document_id:
            # 从数据库获取文档内容
            # 这里需要实现文档查询逻辑
            # document = db.query(Document).filter(Document.id == request.document_id).first()
            # if not document:
            #     raise HTTPException(status_code=404, detail="Document not found")
            # text_to_summarize = document.content

            # 暂时使用向量存储获取文档
            vector_store = get_vector_store()
            chunks = vector_store.get_document_chunks(request.document_id)
            if not chunks:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
                )
            text_to_summarize = " ".join([chunk['content'] for chunk in chunks])

        elif request.text:
            text_to_summarize = request.text
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either document_id or text must be provided",
            )

        result = qa_service.summarize_text(
            text=text_to_summarize, summary_type=request.summary_type, max_length=request.max_length
        )

        return SummarizeResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {str(e)}",
        )


@router.get("/recommend", response_model=RecommendResponse, summary="文档推荐")
async def recommend_documents(
    document_id: Optional[int] = Query(None, description="基准文档ID"),
    query: Optional[str] = Query(None, description="查询文本"),
    limit: int = Query(5, ge=1, le=20, description="推荐数量"),
    similarity_threshold: float = Query(0.5, ge=0.0, le=1.0, description="相似度阈值"),
) -> RecommendResponse:
    """
    获取相关文档推荐

    - **document_id**: 基准文档ID（与query二选一）
    - **query**: 查询文本（与document_id二选一）
    - **limit**: 推荐文档数量
    - **similarity_threshold**: 相似度阈值
    """
    try:
        start_time = time.time()

        if document_id:
            # 基于文档ID推荐
            vector_store = get_vector_store()
            document_chunks = vector_store.get_document_chunks(document_id)
            if not document_chunks:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
                )

            # 使用文档内容作为查询
            query_text = " ".join(
                [chunk['content'] for chunk in document_chunks[:3]]
            )  # 使用前3个块
            base_document = document_chunks[0]['metadata'].get('title', f'Document {document_id}')

        elif query:
            query_text = query
            base_document = None
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either document_id or query must be provided",
            )

        # 执行语义搜索推荐
        search_results = search_engine.search(
            query=query_text,
            limit=limit * 2,  # 搜索更多结果以便过滤
        )

        # 过滤结果
        recommendations = []
        for result in search_results['results']:
            # 过滤掉相同的文档（如果是基于文档ID推荐）
            if document_id and result['id'] == document_id:
                continue

            # 应用相似度阈值
            if result['score'] >= similarity_threshold:
                recommendations.append(result)

            # 达到限制数量就停止
            if len(recommendations) >= limit:
                break

        processing_time = time.time() - start_time

        return RecommendResponse(
            recommendations=recommendations,
            base_document=base_document,
            processing_time=round(processing_time, 3),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Recommendation failed: {str(e)}",
        )


@router.get("/stats", summary="获取知识库统计信息")
async def get_knowledge_stats() -> dict[str, Any]:
    """
    获取知识库统计信息

    返回文档数量、提供商分布、分类统计等信息
    """
    try:
        # 获取向量存储统计
        vector_store = get_vector_store()
        vector_stats = vector_store.get_collection_stats()
        
        # 计算唯一文档数量
        total_documents = 0
        if vector_stats.get('total_chunks', 0) > 0:
            # 获取所有文档ID来计算唯一文档数量
            all_data = vector_store.collection.get(include=['metadatas'])
            unique_doc_ids = set()
            if all_data['metadatas']:
                for metadata in all_data['metadatas']:
                    if isinstance(metadata, dict) and 'document_id' in metadata:
                        unique_doc_ids.add(metadata['document_id'])
            total_documents = len(unique_doc_ids)
        
        # 添加文档总数到统计信息中
        vector_stats['total_documents'] = total_documents

        return {"vector_store": vector_stats, "last_updated": time.time()}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}",
        )
