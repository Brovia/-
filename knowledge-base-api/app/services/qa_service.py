"""
竞品分析问答服务
"""

import logging
import time
import requests
from typing import Any, Optional

from app.core.config import get_settings
from app.models.search import SearchType
from app.services.search_engine import SearchEngine

logger = logging.getLogger(__name__)
settings = get_settings()


class QAService:
    """竞品分析问答服务"""

    def __init__(self) -> None:
        self.search_engine = SearchEngine()

    def answer_question(
        self,
        question: str,
        context_limit: int = 3,
        include_sources: bool = True,
        temperature: float = 0.7,
        provider: Optional[str] = None,
        category: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        回答问题

        Args:
            question: 用户问题
            context_limit: 上下文文档数量
            include_sources: 是否包含来源信息
            temperature: 回答随机性
            provider: 过滤特定云服务提供商
            category: 过滤特定产品分类

        Returns:
            问答响应
        """
        start_time = time.time()

        try:
            # 1. 构建过滤条件
            filters = {}
            if provider:
                filters['provider'] = provider
            if category:
                filters['category'] = category
            
            # 2. 搜索相关文档
            search_results = self.search_engine.search(
                query=question,
                limit=context_limit * 2,  # 搜索更多结果以便筛选
                filters=filters if filters else None,
            )

            if not search_results['results']:
                return {
                    'answer': '抱歉，我在知识库中没有找到相关信息来回答您的问题。',
                    'confidence': 0.0,
                    'sources': [],
                    'processing_time': time.time() - start_time,
                }

            # 2. 选择最相关的文档作为上下文
            relevant_docs = self._select_relevant_context(search_results['results'], context_limit)

            # 3. 生成回答
            answer_data = self._generate_template_answer(question, relevant_docs)

            # 4. 准备来源信息
            sources = []
            if include_sources:
                sources = self._prepare_sources(relevant_docs, question)

            processing_time = time.time() - start_time

            return {
                'answer': answer_data['answer'],
                'confidence': answer_data['confidence'],
                'sources': sources,
                'processing_time': round(processing_time, 3),
            }

        except Exception as e:
            logger.error(f"Failed to answer question: {str(e)}")
            return {
                'answer': '抱歉，处理您的问题时发生了错误，请稍后重试。',
                'confidence': 0.0,
                'sources': [],
                'processing_time': time.time() - start_time,
                'error': str(e),
            }

    def _select_relevant_context(self, search_results: list[dict], limit: int) -> list[dict]:
        """选择最相关的上下文文档"""
        # 按分数排序并去重
        seen_docs = set()
        relevant_docs: list[dict[str, Any]] = []

        for result in search_results:
            doc_id = result['id']
            if doc_id not in seen_docs and len(relevant_docs) < limit:
                seen_docs.add(doc_id)
                relevant_docs.append(result)

        return relevant_docs



    def _generate_template_answer(self, question: str, context_docs: list[dict]) -> dict[str, Any]:
        """生成模板化竞品分析回答"""
        try:
            if not context_docs:
                return {
                    'answer': '抱歉，我在知识库中没有找到相关信息来进行竞品分析。',
                    'confidence': 0.0,
                }

            # 分析问题类型
            question_lower = question.lower()

            # 构建竞品分析回答
            answer_parts = []

            if any(keyword in question_lower for keyword in ['什么是', 'what is', '定义', '介绍']):
                # 定义类问题
                best_doc = context_docs[0]
                answer_parts.append(f"根据知识库信息，{best_doc['title']}的相关内容如下：")
                answer_parts.append(best_doc['content'][:800] + "...")

            elif any(
                keyword in question_lower for keyword in ['区别', '差异', '对比', 'vs', '比较', '竞品', '对比分析']
            ):
                # 竞品对比类问题
                answer_parts.append("基于知识库信息，各厂商产品对比如下：")
                
                # 按厂商分组
                providers = {}
                for doc in context_docs:
                    provider = doc['metadata'].get('provider', '未知厂商')
                    if provider not in providers:
                        providers[provider] = []
                    providers[provider].append(doc)
                
                for provider, docs in list(providers.items())[:3]:  # 最多3个厂商
                    answer_parts.append(f"\n【{provider}】")
                    for doc in docs[:2]:  # 每个厂商最多2个文档
                        answer_parts.append(f"• {doc['title']}")
                        answer_parts.append(f"  {doc['content'][:300]}...")

            elif any(keyword in question_lower for keyword in ['如何', 'how', '怎么', '步骤', '配置']):
                # 操作类问题
                answer_parts.append("基于知识库内容，相关操作说明如下：")
                answer_parts.append(context_docs[0]['content'][:800] + "...")

            else:
                # 通用竞品分析问题
                answer_parts.append("根据知识库搜索结果，竞品分析如下：")
                
                # 按厂商分组展示
                providers = {}
                for doc in context_docs:
                    provider = doc['metadata'].get('provider', '未知厂商')
                    if provider not in providers:
                        providers[provider] = []
                    providers[provider].append(doc)
                
                for provider, docs in list(providers.items())[:3]:
                    answer_parts.append(f"\n【{provider}产品分析】")
                    for doc in docs[:2]:
                        answer_parts.append(f"• {doc['title']}")
                        answer_parts.append(f"  {doc['content'][:300]}...")

            answer = '\n'.join(answer_parts)

            # 计算置信度
            confidence = min(0.8, len(context_docs) * 0.25 + context_docs[0]['score'] * 0.3)

            return {'answer': answer, 'confidence': confidence}

        except Exception as e:
            logger.error(f"Template answer generation failed: {str(e)}")
            return {'answer': '抱歉，生成竞品分析时发生错误。', 'confidence': 0.0}

    def _calculate_answer_confidence(
        self, question: str, answer: str, context_docs: list[dict]
    ) -> float:
        """计算回答置信度"""
        try:
            confidence_factors = []

            # 1. 基于搜索结果分数
            if context_docs:
                avg_search_score = sum(doc['score'] for doc in context_docs) / len(context_docs)
                confidence_factors.append(avg_search_score * 0.4)

            # 2. 基于回答长度（适当长度表示有足够信息）
            answer_length_factor = min(1.0, len(answer.split()) / 100)
            confidence_factors.append(answer_length_factor * 0.2)

            # 3. 基于关键词匹配
            question_keywords = set(question.lower().split())
            answer_keywords = set(answer.lower().split())
            keyword_overlap = len(question_keywords.intersection(answer_keywords)) / len(
                question_keywords
            )
            confidence_factors.append(keyword_overlap * 0.2)

            # 4. 基于是否包含否定词（如"没有找到"、"不确定"等）
            negative_phrases = ['没有找到', '不确定', '不清楚', '无法确定', '抱歉']
            has_negative = any(phrase in answer for phrase in negative_phrases)
            if has_negative:
                confidence_factors.append(0.1)
            else:
                confidence_factors.append(0.2)

            # 计算总置信度
            total_confidence: float = sum(confidence_factors)

            return min(1.0, max(0.0, total_confidence))

        except Exception:
            return 0.5  # 默认中等置信度

    def _prepare_sources(self, context_docs: list[dict], question: str) -> list[dict[str, Any]]:
        """准备来源信息"""
        sources = []

        for doc in context_docs:
            # 提取相关片段
            content = doc['content']
            excerpt = content[:300] + "..." if len(content) > 300 else content

            # 计算相关性
            relevance = doc['score']

            source = {
                'document': doc.get('source', doc.get('title', 'Unknown')),
                'excerpt': excerpt,
                'relevance': round(relevance, 3),
            }

            # 添加额外元数据
            if doc.get('metadata'):
                source['provider'] = doc['metadata'].get('provider', '')
                source['source_url'] = doc['metadata'].get('source_url', '')

            sources.append(source)

        return sources

    def summarize_text(
        self, text: str, summary_type: str = "brief", max_length: int = 200
    ) -> dict[str, Any]:
        """
        文本摘要

        Args:
            text: 待摘要文本
            summary_type: 摘要类型 (brief/detailed)
            max_length: 最大摘要长度

        Returns:
            摘要响应
        """
        try:
            original_length = len(text)

            summary = self._generate_template_summary(text, summary_type, max_length)

            summary_length = len(summary)
            compression_ratio = summary_length / original_length if original_length > 0 else 0

            return {
                'summary': summary,
                'original_length': original_length,
                'summary_length': summary_length,
                'compression_ratio': round(compression_ratio, 3),
            }

        except Exception as e:
            logger.error(f"Text summarization failed: {str(e)}")
            return {
                'summary': text[:max_length] + "..." if len(text) > max_length else text,
                'original_length': len(text),
                'summary_length': min(len(text), max_length),
                'compression_ratio': min(1.0, max_length / len(text)) if len(text) > 0 else 0,
                'error': str(e),
            }



    def _generate_template_summary(self, text: str, summary_type: str, max_length: int) -> str:
        """生成模板化摘要"""
        try:
            # 简单的摘要策略：提取前几句话和关键信息
            sentences = text.split('。')
            sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

            if summary_type == "brief":
                # 简洁摘要：取前2-3句
                summary_sentences = sentences[:3]
            else:
                # 详细摘要：取前5-7句
                summary_sentences = sentences[:7]

            summary = '。'.join(summary_sentences)
            if not summary.endswith('。'):
                summary += '。'

            # 确保长度限制
            if len(summary) > max_length:
                summary = summary[: max_length - 3] + "..."

            return summary

        except Exception:
            # 最后的fallback
            return text[: max_length - 3] + "..." if len(text) > max_length else text
