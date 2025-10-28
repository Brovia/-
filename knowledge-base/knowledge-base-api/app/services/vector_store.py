"""
向量存储服务
"""

import logging
import math
from typing import Any, Optional

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings
from FlagEmbedding import FlagModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class VectorStore:
    """向量存储管理器"""

    def __init__(self) -> None:
        self.client: Optional[chromadb.ClientAPI] = None
        self.collection: Optional[Collection] = None
        self.embedding_model: Optional[FlagModel] = None
        self._initialize()

    def _initialize(self) -> None:
        """初始化向量存储"""
        try:
            # 初始化ChromaDB客户端
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )

            # 立即加载嵌入模型，确保健康检查能正确识别
            logger.info("Loading embedding model...")
            self.embedding_model = FlagModel(
                settings.EMBEDDING_MODEL, 
                query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章："
            )
            
            # 获取模型的向量维度
            test_embedding = self.embedding_model.encode(["test"]).tolist()[0]
            embedding_dimension = len(test_embedding)
            logger.info(f"Embedding model dimension: {embedding_dimension}")
            
            # 尝试获取现有集合
            collection_exists = False
            try:
                self.collection = self.client.get_collection(name="knowledge_base")
                collection_exists = True
                logger.info("Using existing collection 'knowledge_base'")
                
                # 检查现有集合的维度是否匹配
                existing_count = self.collection.count()
                if existing_count > 0:
                    # 如果集合中有数据，获取一个样本来检查维度
                    try:
                        sample = self.collection.peek(limit=1)
                        embeddings_list = sample.get('embeddings')
                        if embeddings_list is not None and len(embeddings_list) > 0 and len(embeddings_list[0]) > 0:
                            existing_dimension = len(embeddings_list[0])
                            if existing_dimension != embedding_dimension:
                                logger.warning(
                                    f"Dimension mismatch detected: existing collection has dimension {existing_dimension}, "
                                    f"but current model produces dimension {embedding_dimension}. "
                                    f"Recreating collection..."
                                )
                                # 删除旧集合并创建新的
                                self.client.delete_collection("knowledge_base")
                                self.collection = self.client.create_collection(
                                    name="knowledge_base", 
                                    metadata={
                                        "description": "Knowledge base document chunks",
                                        "embedding_model": settings.EMBEDDING_MODEL,
                                        "embedding_dimension": embedding_dimension
                                    }
                                )
                                logger.info(f"Created new collection with dimension {embedding_dimension}")
                    except Exception as check_error:
                        logger.warning(f"Could not check existing dimension: {str(check_error)}. Continuing with existing collection.")
                        
            except Exception as e:
                # 集合不存在，创建新的
                if not collection_exists:
                    self.collection = self.client.create_collection(
                        name="knowledge_base", 
                        metadata={
                            "description": "Knowledge base document chunks",
                            "embedding_model": settings.EMBEDDING_MODEL,
                            "embedding_dimension": embedding_dimension
                        }
                    )
                    logger.info(f"Created new collection 'knowledge_base' with dimension {embedding_dimension}")
                else:
                    raise
            
            logger.info(f"Vector store initialized successfully with embedding model: {settings.EMBEDDING_MODEL}")

        except Exception as e:
            logger.error(f"Failed to initialize vector store: {str(e)}")
            raise

    def _ensure_embedding_model(self) -> None:
        """惰性加载嵌入模型"""
        if self.embedding_model is None:
            try:
                self.embedding_model = FlagModel(
                    settings.EMBEDDING_MODEL, 
                    query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章："
                )
                logger.info("Embedding model loaded successfully")
            except Exception as e:
                logger.error(
                    f"Failed to load embedding model '{settings.EMBEDDING_MODEL}': {str(e)}"
                )
                raise

    def add_document(
        self, document_id: int, chunks: list[dict[str, Any]], metadata: Optional[dict[str, Any]] = None
    ) -> bool:
        """
        添加文档到向量存储

        Args:
            document_id: 文档ID
            chunks: 文档块列表
            metadata: 文档元数据

        Returns:
            是否成功添加
        """
        try:
            if not chunks:
                logger.warning(f"No chunks to add for document {document_id}")
                return True

            # 记录传入的元数据
            logger.info(f"Adding document {document_id} with metadata: provider='{metadata.get('provider') if metadata else None}', category='{metadata.get('category') if metadata else None}'")

            # 准备数据
            texts = []
            ids = []
            metadatas = []

            for chunk in chunks:
                chunk_id = f"doc_{document_id}_chunk_{chunk['chunk_index']}"

                # 文本内容
                texts.append(chunk['content'])
                ids.append(chunk_id)

                # 元数据
                chunk_metadata = {
                    'document_id': document_id,
                    'chunk_index': chunk['chunk_index'],
                    'start_pos': chunk['start_pos'],
                    'end_pos': chunk['end_pos'],
                    'word_count': chunk['word_count'],
                }

                # 添加文档级别的元数据
                if metadata:
                    chunk_metadata.update(
                        {
                            'title': metadata.get('title', ''),
                            'provider': metadata.get('provider', ''),
                            'category': metadata.get('category', ''),
                            'source_url': metadata.get('source_url', ''),
                            'filename': metadata.get('filename', ''),
                        }
                    )

                metadatas.append(chunk_metadata)
            
            # 记录第一个chunk的元数据用于调试
            if metadatas:
                logger.info(f"First chunk metadata: provider='{metadatas[0].get('provider')}', category='{metadatas[0].get('category')}')")

            # 生成嵌入向量（惰性加载模型）
            self._ensure_embedding_model()
            if self.embedding_model is None:
                raise RuntimeError("Embedding model not available")
            embeddings = self.embedding_model.encode(texts).tolist()

            # 添加到集合
            if self.collection is None:
                raise RuntimeError("Collection not available")
            # 类型转换以兼容ChromaDB的类型要求
            metadatas_typed = [dict(meta) for meta in metadatas]
            self.collection.add(
                embeddings=embeddings, 
                documents=texts, 
                metadatas=metadatas_typed,  # type: ignore
                ids=ids
            )

            logger.info(f"Added {len(chunks)} chunks for document {document_id} to vector store")
            return True

        except Exception as e:
            logger.error(f"Failed to add document {document_id} to vector store: {str(e)}")
            return False

    def search_similar(
        self, query: str, limit: int = 10, filter_criteria: Optional[dict[str, Any]] = None
    ) -> list[dict[str, Any]]:
        """
        语义相似度搜索

        Args:
            query: 查询文本
            limit: 返回结果数量
            filter_criteria: 过滤条件

        Returns:
            搜索结果列表
        """
        try:
            # 生成查询向量（惰性加载模型）
            self._ensure_embedding_model()
            if self.embedding_model is None:
                raise RuntimeError("Embedding model not available")
            query_embedding = self.embedding_model.encode([query]).tolist()

            # 构建过滤条件
            where_clause = None
            if filter_criteria:
                # 过滤掉None值
                valid_filters = {key: value for key, value in filter_criteria.items() if value is not None}
                
                if len(valid_filters) == 1:
                    # 单个过滤条件
                    where_clause = valid_filters
                elif len(valid_filters) > 1:
                    # 多个过滤条件，使用$and操作符
                    where_clause = {
                        '$and': [{key: value} for key, value in valid_filters.items()]
                    }

            # 执行搜索
            if self.collection is None:
                raise RuntimeError("Collection not available")
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=limit,
                where=where_clause,
                include=['metadatas', 'documents', 'distances'],
            )

            # 格式化结果
            formatted_results = []
            
            # 计算查询长度惩罚因子（调整为更宽松的惩罚）
            # 短query会被轻微惩罚
            query_length = len(query.strip())
            if query_length <= 2:
                length_penalty = 0.8  # 1-2个字的query，得分减20%
            elif query_length <= 4:
                length_penalty = 0.9  # 3-4个字的query，得分减10%
            else:
                length_penalty = 1.0  # 5个字以上不惩罚

            if results['ids'] and len(results['ids']) > 0:
                ids_list = results['ids'][0] if results['ids'] else []
                documents_list = results['documents'][0] if results['documents'] else []
                metadatas_list = results['metadatas'][0] if results['metadatas'] else []
                distances_list = results['distances'][0] if results['distances'] else []
                
                for i in range(len(ids_list)):
                    # 将L2距离转换为相似度分数 [0, 1]，距离越小分数越高
                    # 使用温和的指数衰减函数
                    # 公式: base_score = exp(-distance^2 * 0.5)
                    # 使用较小系数0.5使衰减更温和，提高搜索召回率
                    # 这样：distance=0.0 -> score=1.0 (完全匹配)
                    #       distance=0.5 -> score=0.88
                    #       distance=1.0 -> score=0.61
                    #       distance=1.5 -> score=0.32
                    #       distance=2.0 -> score=0.14
                    distance = distances_list[i]
                    base_score = math.exp(-(distance ** 2) * 0.5)
                    
                    # 应用查询长度惩罚
                    final_score = base_score * length_penalty
                    
                    result = {
                        'id': ids_list[i],
                        'content': documents_list[i],
                        'metadata': metadatas_list[i],
                        'score': final_score,
                        'document_id': metadatas_list[i].get('document_id') if isinstance(metadatas_list[i], dict) else None,
                        'chunk_index': metadatas_list[i].get('chunk_index') if isinstance(metadatas_list[i], dict) else None,
                    }
                    formatted_results.append(result)

            logger.info(f"Found {len(formatted_results)} similar results for query (length: {query_length}, penalty: {length_penalty})")
            return formatted_results

        except Exception as e:
            logger.error(f"Failed to search similar documents: {str(e)}")
            return []

    def get_document_chunks(self, document_id: int) -> list[dict[str, Any]]:
        """
        获取文档的所有块

        Args:
            document_id: 文档ID

        Returns:
            文档块列表
        """
        try:
            if self.collection is None:
                raise RuntimeError("Collection not available")
            results = self.collection.get(
                where={"document_id": document_id}, include=['metadatas', 'documents']
            )

            chunks = []
            if results['ids']:
                ids_list = results['ids'] if results['ids'] else []
                documents_list = results['documents'] if results['documents'] else []
                metadatas_list = results['metadatas'] if results['metadatas'] else []
                
                for i in range(len(ids_list)):
                    chunk = {
                        'id': ids_list[i],
                        'content': documents_list[i],
                        'metadata': metadatas_list[i],
                    }
                    chunks.append(chunk)

            # 按chunk_index排序
            chunks.sort(key=lambda x: x['metadata'].get('chunk_index', 0) if isinstance(x['metadata'], dict) else 0)

            return chunks

        except Exception as e:
            logger.error(f"Failed to get chunks for document {document_id}: {str(e)}")
            return []

    def delete_document(self, document_id: int) -> bool:
        """
        删除文档的所有向量

        Args:
            document_id: 文档ID

        Returns:
            是否成功删除
        """
        try:
            if self.collection is None:
                raise RuntimeError("Collection not available")
            # 获取文档的所有chunk IDs
            results = self.collection.get(where={"document_id": document_id}, include=['metadatas'])

            if results['ids']:
                # 删除所有相关的chunks
                self.collection.delete(ids=results['ids'])
                logger.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")

            return True

        except Exception as e:
            logger.error(f"Failed to delete document {document_id} from vector store: {str(e)}")
            return False

    def update_document(
        self, document_id: int, chunks: list[dict[str, Any]], metadata: Optional[dict[str, Any]] = None
    ) -> bool:
        """
        更新文档向量

        Args:
            document_id: 文档ID
            chunks: 新的文档块列表
            metadata: 文档元数据

        Returns:
            是否成功更新
        """
        try:
            # 先删除旧的向量
            self.delete_document(document_id)

            # 添加新的向量
            return self.add_document(document_id, chunks, metadata)

        except Exception as e:
            logger.error(f"Failed to update document {document_id} in vector store: {str(e)}")
            return False

    def get_collection_stats(self) -> dict[str, Any]:
        """获取集合统计信息"""
        try:
            if self.collection is None:
                raise RuntimeError("Collection not available")
            count = self.collection.count()

            # 获取所有数据来分析提供商和分类分布
            all_data = self.collection.get(include=['metadatas'])

            providers = set()
            categories = set()
            provider_counts = {}
            category_counts = {}

            if all_data['metadatas']:
                for metadata in all_data['metadatas']:
                    if isinstance(metadata, dict):
                        provider = metadata.get('provider', '').strip()
                        category = metadata.get('category', '').strip()
                        
                        if provider:
                            providers.add(provider)
                            provider_counts[provider] = provider_counts.get(provider, 0) + 1
                        
                        if category:
                            categories.add(category)
                            category_counts[category] = category_counts.get(category, 0) + 1

            # 计算提供商百分比
            provider_percentages = {}
            if provider_counts:
                total_chunks = sum(provider_counts.values())
                for provider, provider_count in provider_counts.items():
                    percentage = round((provider_count / total_chunks) * 100, 1)
                    provider_percentages[provider] = {
                        'count': provider_count,
                        'percentage': percentage
                    }

            return {
                'total_chunks': count,
                'providers': list(providers),
                'categories': list(categories),
                'provider_distribution': provider_percentages,
                'category_distribution': category_counts,
                'embedding_model': settings.EMBEDDING_MODEL,
                'collection_name': self.collection.name,
            }

        except Exception as e:
            logger.error(f"Failed to get collection stats: {str(e)}")
            return {}

    def reset_collection(self) -> bool:
        """重置集合（删除所有数据）"""
        try:
            if self.client is None:
                raise RuntimeError("Client not available")
            self.client.delete_collection("knowledge_base")
            self.collection = self.client.create_collection(
                name="knowledge_base", metadata={"description": "Knowledge base document chunks"}
            )
            logger.info("Vector store collection reset successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to reset collection: {str(e)}")
            return False
