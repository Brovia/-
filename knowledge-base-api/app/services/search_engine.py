"""
搜索引擎服务
"""

import time
from typing import Any, Optional

import logging
from dataclasses import dataclass

from app.core.config import get_settings
from app.models.search import SearchType
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class SearchConfig:
    """搜索配置"""

    min_score_threshold: float = 0.1  # 降低阈值，避免过度过滤结果
    max_results_per_source: int = 100


class SearchEngine:
    """向量搜索引擎"""

    def __init__(self) -> None:
        self.vector_store = VectorStore()
        self.config = SearchConfig()

    def semantic_search(
        self, query: str, limit: int = 10, filters: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """语义搜索"""
        try:
            return self.vector_store.search_similar(query, limit, filters)
        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}")
            return []

    def search(
        self,
        query: str,
        limit: int = 10,
        filters: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        语义搜索接口

        Args:
            query: 搜索查询
            limit: 返回结果数量
            filters: 过滤条件

        Returns:
            搜索响应
        """
        start_time = time.time()

        try:
            # 使用语义搜索
            results = self.semantic_search(query, limit, filters)

            processing_time = time.time() - start_time

            # 格式化为标准响应格式，并过滤低分结果
            formatted_results = []
            for result in results:
                # 过滤掉相似度低于阈值的结果
                if result['score'] < self.config.min_score_threshold:
                    logger.debug(f"Filtered out result with score {result['score']} (threshold: {self.config.min_score_threshold})")
                    continue
                    
                formatted_result = {
                    'id': result['metadata']['document_id'],
                    'title': result['metadata'].get('title', ''),
                    'content': (
                        result['content'][:500] + '...'
                        if len(result['content']) > 500
                        else result['content']
                    ),
                    'source': result['metadata'].get('filename', ''),
                    'score': result['score'],
                    'metadata': result['metadata'],
                    'highlight': [],  # 向量搜索不提供高亮
                }
                formatted_results.append(formatted_result)

            return {
                'total': len(formatted_results),
                'results': formatted_results,
                'query': query,
                'search_type': 'semantic',
                'processing_time': round(processing_time, 3),
            }

        except Exception as e:
            logger.error(f"Search failed for query '{query}': {str(e)}")
            return {
                'total': 0,
                'results': [],
                'query': query,
                'search_type': 'semantic',
                'processing_time': time.time() - start_time,
                'error': str(e),
            }