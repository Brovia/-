"""
基于LangChain的文档处理服务
"""

import hashlib
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from langchain_community.document_loaders import (
    TextLoader, UnstructuredMarkdownLoader, DirectoryLoader,
    UnstructuredPDFLoader, UnstructuredWordDocumentLoader,
    UnstructuredExcelLoader, UnstructuredPowerPointLoader
)
from langchain_core.documents import Document as LangChainDocument
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DocumentProcessor:
    """基于LangChain的文档处理器"""

    def __init__(
        self, 
        chunk_size: Optional[int] = None, 
        chunk_overlap: Optional[int] = None,
        separators: Optional[List[str]] = None
    ):
        """
        初始化文档处理器
        
        Args:
            chunk_size: 文本块大小，默认使用配置中的值
            chunk_overlap: 文本块重叠大小，默认使用配置中的值
            separators: 文本分割符，默认使用配置中的值
        """
        self.chunk_size = chunk_size or settings.DOCUMENT_CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.DOCUMENT_CHUNK_OVERLAP
        self.separators = separators or settings.DOCUMENT_SEPARATORS
        
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
            length_function=len,
            is_separator_regex=False,
        )
        
        logger.info(f"LangChain DocumentProcessor initialized with chunk_size={self.chunk_size}, chunk_overlap={self.chunk_overlap}")

    def process_file(self, file_path: str) -> dict[str, Any]:
        """
        处理单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            处理后的文档数据
        """
        try:
            # 使用LangChain加载器加载文档
            langchain_docs = self._load_document(file_path)
            
            if not langchain_docs:
                raise ValueError(f"No content loaded from {file_path}")
            
            # 合并所有文档内容
            combined_content = "\n\n".join([doc.page_content for doc in langchain_docs])
            combined_metadata = self._merge_metadata(langchain_docs)
            
            # 添加文件信息
            file_info = self._get_file_info(file_path)
            
            # 提取元数据
            extracted_metadata = self._extract_metadata(combined_content, file_path)
            combined_metadata.update(extracted_metadata)
            
            # 使用LangChain分割文本
            chunks = self._split_text_with_langchain(combined_content, file_path)
            
            # 计算内容哈希
            content_hash = self._calculate_hash(combined_content)
            
            result = {
                'title': self._extract_title(combined_content, file_path),
                'content': combined_content,
                'raw_content': combined_content,  # LangChain已经处理了原始内容
                'frontmatter': {},  # LangChain处理后的文档可能没有frontmatter
                'html_content': '',  # 不再需要HTML内容
                'metadata': combined_metadata,
                'chunks': chunks,
                'content_hash': content_hash,
                **file_info
            }
            
            logger.info(f"Successfully processed file with LangChain: {file_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing file {file_path} with LangChain: {str(e)}")
            raise

    def _load_document(self, file_path: str) -> List[LangChainDocument]:
        """
        使用LangChain加载器加载文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            LangChain文档列表
        """
        try:
            file_path_obj = Path(file_path)
            file_ext = file_path_obj.suffix.lower()
            
            # 根据文件扩展名选择合适的加载器
            if file_ext == '.md':
                loader = UnstructuredMarkdownLoader(file_path)
            elif file_ext == '.pdf':
                loader = UnstructuredPDFLoader(file_path)
            elif file_ext in ['.doc', '.docx']:
                loader = UnstructuredWordDocumentLoader(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                loader = UnstructuredExcelLoader(file_path)
            elif file_ext in ['.pptx', '.ppt']:
                loader = UnstructuredPowerPointLoader(file_path)
            elif file_ext == '.txt':
                loader = TextLoader(file_path, encoding='utf-8')
            else:
                # 对于其他文件，尝试使用TextLoader
                loader = TextLoader(file_path, encoding='utf-8')
            
            # 加载文档
            documents = loader.load()
            
            logger.info(f"Loaded {len(documents)} document(s) from {file_path} using {file_ext} loader")
            return documents
            
        except Exception as e:
            logger.error(f"Failed to load document {file_path}: {str(e)}")
            raise

    def _merge_metadata(self, documents: List[LangChainDocument]) -> dict[str, Any]:
        """
        合并多个文档的元数据
        
        Args:
            documents: LangChain文档列表
            
        Returns:
            合并后的元数据
        """
        merged_metadata = {}
        
        for doc in documents:
            if doc.metadata:
                merged_metadata.update(doc.metadata)
        
        return merged_metadata

    def _extract_title(self, content: str, file_path: str = None) -> str:
        """从内容中提取标题，优先使用文件名"""
        # 如果有文件路径，优先使用文件名（不包含扩展名）
        if file_path:
            filename = Path(file_path).name
            if '.' in filename:
                return filename.rsplit('.', 1)[0]
            return filename
        
        # 查找第一个一级标题
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()

        # 如果没有一级标题，查找二级标题
        title_match = re.search(r'^##\s+(.+)$', content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()

        # 如果都没有，返回默认标题
        return "Untitled Document"

    def _get_file_info(self, file_path: str) -> dict[str, Any]:
        """获取文件信息"""
        path_obj = Path(file_path)
        stat = path_obj.stat()

        return {
            'filename': path_obj.name,
            'file_path': str(path_obj.absolute()),
            'file_size': stat.st_size,
            'created_at': datetime.fromtimestamp(stat.st_ctime),
            'modified_at': datetime.fromtimestamp(stat.st_mtime),
        }

    def _extract_metadata(self, content: str, file_path: str) -> dict[str, Any]:
        """提取文档元数据"""
        metadata = {}

        # 首先从文件路径中提取提供商和分类信息
        # 文件路径格式: /path/to/documents/云厂商/产品分类/文件名.md
        path_obj = Path(file_path)
        path_parts = path_obj.parts
        
        # 尝试从路径中提取提供商和分类
        # 查找documents目录后的路径部分
        try:
            if 'documents' in path_parts:
                doc_index = path_parts.index('documents')
                if len(path_parts) > doc_index + 1:
                    # documents后的第一个目录是提供商
                    path_provider = path_parts[doc_index + 1]
                    if path_provider in ['阿里云', '腾讯云', 'AWS', 'Azure', 'GCP', '华为云', '火山云']:
                        metadata['provider'] = path_provider
                    
                if len(path_parts) > doc_index + 2:
                    # documents后的第二个目录是分类
                    path_category = path_parts[doc_index + 2]
                    metadata['category'] = path_category
        except (ValueError, IndexError):
            pass

        # 如果从路径中没有提取到提供商，则从内容中检测
        if 'provider' not in metadata:
            # 云服务提供商检测
            if '阿里云' in content or 'ALB' in content or 'aliyun' in content.lower():
                metadata['provider'] = '阿里云'
            elif '腾讯云' in content or 'tencent' in content.lower():
                metadata['provider'] = '腾讯云'
            elif 'GCP' in content or 'google cloud' in content.lower():
                metadata['provider'] = 'GCP'
            elif 'azure' in content.lower() or '微软' in content:
                metadata['provider'] = 'Azure'
            elif 'aws' in content.lower() or 'amazon' in content.lower():
                metadata['provider'] = 'AWS'
            elif '华为云' in content or 'huawei' in content.lower():
                metadata['provider'] = '华为云'
            elif '火山云' in content:
                metadata['provider'] = '火山云'

        # 如果从路径中没有提取到分类，则从内容中检测
        if 'category' not in metadata:
            # 技术分类
            if '负载均衡' in content or 'load balancer' in content.lower():
                metadata['category'] = '负载均衡'
        
        # 设置标签
        if metadata.get('category') == '负载均衡':
            metadata['tags'] = '负载均衡,网络,高可用'

        # 从内容中提取源链接
        url_pattern = r'> 来源:\s*(https?://[^\s\n]+)'
        url_match = re.search(url_pattern, content)
        if url_match:
            metadata['source_url'] = url_match.group(1)

        # 提取转换时间
        time_pattern = r'> 转换时间:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})'
        time_match = re.search(time_pattern, content)
        if time_match:
            metadata['converted_at'] = time_match.group(1)

        # 统计信息
        metadata['word_count'] = str(len(content.split()))
        metadata['char_count'] = str(len(content))

        return metadata

    def _split_text_with_langchain(self, text: str, file_path: str) -> List[dict[str, Any]]:
        """
        使用LangChain分割文本
        
        Args:
            text: 要分割的文本
            file_path: 文件路径（用于元数据）
            
        Returns:
            分割后的文本块列表
        """
        if not text:
            return []

        try:
            # 创建LangChain文档对象
            doc = LangChainDocument(page_content=text, metadata={"source": file_path})
            
            # 使用LangChain分割器分割文档
            split_docs = self.text_splitter.split_documents([doc])
            
            # 转换为原有格式
            chunks = []
            for i, split_doc in enumerate(split_docs):
                chunk = {
                    'content': split_doc.page_content,
                    'chunk_index': i,
                    'start_pos': 0,  # LangChain不提供精确的位置信息
                    'end_pos': len(split_doc.page_content),
                    'word_count': len(split_doc.page_content.split()),
                    'metadata': split_doc.metadata.copy() if split_doc.metadata else {}
                }
                chunks.append(chunk)
            
            logger.info(f"Split text into {len(chunks)} chunks using LangChain")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to split text with LangChain: {str(e)}")
            # 回退到简单分割
            return self._fallback_split_text(text)

    def _fallback_split_text(self, text: str) -> List[dict[str, Any]]:
        """
        回退的简单文本分割方法
        
        Args:
            text: 要分割的文本
            
        Returns:
            分割后的文本块列表
        """
        if not text:
            return []

        words = text.split()
        if len(words) <= self.chunk_size:
            return [{
                'content': text,
                'chunk_index': 0,
                'start_pos': 0,
                'end_pos': len(text),
                'word_count': len(words),
                'metadata': {}
            }]

        chunks = []
        start_idx = 0
        chunk_index = 0

        while start_idx < len(words):
            end_idx = min(start_idx + self.chunk_size, len(words))
            chunk_words = words[start_idx:end_idx]
            chunk_text = ' '.join(chunk_words)

            start_pos = len(' '.join(words[:start_idx]))
            if start_idx > 0:
                start_pos += 1
            end_pos = start_pos + len(chunk_text)

            chunks.append({
                'content': chunk_text,
                'chunk_index': chunk_index,
                'start_pos': start_pos,
                'end_pos': end_pos,
                'word_count': len(chunk_words),
                'metadata': {}
            })

            start_idx = end_idx - self.chunk_overlap
            if start_idx >= end_idx:
                break
            chunk_index += 1

        return chunks

    def _calculate_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def batch_process_directory(
        self, directory: str, file_extension: str = "*.md"
    ) -> List[dict[str, Any]]:
        """
        批量处理目录中的文件
        
        Args:
            directory: 目录路径
            file_extension: 文件扩展名模式，支持 "*.md", "*.pdf", "*.doc", "*.docx", "*.txt", "*.xlsx", "*.xls", "*.pptx", "*.ppt"
            
        Returns:
            处理后的文档列表
        """
        directory_path = Path(directory)
        if not directory_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        # 使用LangChain的DirectoryLoader
        try:
            # 根据文件扩展名选择加载器
            if file_extension == "*.md":
                loader_cls = UnstructuredMarkdownLoader
            elif file_extension == "*.pdf":
                loader_cls = UnstructuredPDFLoader
            elif file_extension in ["*.doc", "*.docx"]:
                loader_cls = UnstructuredWordDocumentLoader
            elif file_extension in ["*.xlsx", "*.xls"]:
                loader_cls = UnstructuredExcelLoader
            elif file_extension in ["*.pptx", "*.ppt"]:
                loader_cls = UnstructuredPowerPointLoader
            else:
                loader_cls = TextLoader
            
            loader = DirectoryLoader(
                directory, 
                glob=file_extension,
                loader_cls=loader_cls,
                loader_kwargs={"encoding": "utf-8"} if loader_cls == TextLoader else {}
            )
            
            # 加载所有文档
            all_docs = loader.load()
            
            processed_documents = []
            for i, doc in enumerate(all_docs):
                try:
                    # 为每个文档创建临时文件路径（用于元数据）
                    temp_file_path = doc.metadata.get('source', f'temp_doc_{i}.md')
                    
                    # 处理文档
                    doc_data = self._process_single_document(doc, temp_file_path)
                    processed_documents.append(doc_data)
                    
                except Exception as e:
                    logger.error(f"Failed to process document {i}: {str(e)}")
                    continue

            logger.info(f"Processed {len(processed_documents)} documents from {directory} using LangChain")
            return processed_documents
            
        except Exception as e:
            logger.error(f"Failed to batch process directory with LangChain: {str(e)}")
            # 回退到逐个文件处理
            return self._fallback_batch_process(directory, file_extension)

    def _process_single_document(self, doc: LangChainDocument, file_path: str) -> dict[str, Any]:
        """
        处理单个LangChain文档
        
        Args:
            doc: LangChain文档对象
            file_path: 文件路径
            
        Returns:
            处理后的文档数据
        """
        content = doc.page_content
        metadata = doc.metadata.copy() if doc.metadata else {}
        
        # 添加文件信息
        file_info = self._get_file_info(file_path)
        
        # 提取元数据
        extracted_metadata = self._extract_metadata(content, file_path)
        metadata.update(extracted_metadata)
        
        # 分割文本
        chunks = self._split_text_with_langchain(content, file_path)
        
        # 计算内容哈希
        content_hash = self._calculate_hash(content)
        
        return {
            'title': self._extract_title(content),
            'content': content,
            'raw_content': content,
            'frontmatter': {},
            'html_content': '',
            'metadata': metadata,
            'chunks': chunks,
            'content_hash': content_hash,
            **file_info
        }

    def _fallback_batch_process(
        self, directory: str, file_extension: str = "*.md"
    ) -> List[dict[str, Any]]:
        """
        回退的批量处理方法
        
        Args:
            directory: 目录路径
            file_extension: 文件扩展名模式
            
        Returns:
            处理后的文档列表
        """
        directory_path = Path(directory)
        files = list(directory_path.glob(file_extension))

        processed_documents = []
        for file_path in files:
            try:
                doc_data = self.process_file(str(file_path))
                processed_documents.append(doc_data)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {str(e)}")
                continue

        logger.info(f"Processed {len(processed_documents)} documents from {directory} (fallback method)")
        return processed_documents

    def is_content_changed(self, file_path: str, stored_hash: str) -> bool:
        """检查文件内容是否发生变化"""
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            current_hash = self._calculate_hash(content)
            return current_hash != stored_hash
        except Exception as e:
            logger.error(f"Error checking file changes for {file_path}: {str(e)}")
            return True  # 如果无法检查，假设已更改

    def get_processor_info(self) -> dict[str, Any]:
        """获取处理器信息"""
        return {
            'type': 'LangChain',
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'separators': self.separators,
            'version': '1.0.0'
        }
