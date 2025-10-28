"""
管理API端点
"""

import logging
import shutil
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.document import Document, DocumentResponse, DocumentStatus
from app.services.document_processor import DocumentProcessor
from app.services.health_service import HealthService
from app.services.search_engine import SearchEngine
from app.services.vector_store import VectorStore

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)

# 初始化服务
document_processor = DocumentProcessor()

# 懒加载vector_store，避免模块加载时的集合ID缓存问题
def get_vector_store():
    return VectorStore()

def get_search_engine():
    return SearchEngine()

def get_health_service():
    return HealthService(get_vector_store())


@router.get("/documents", summary="获取文档列表")
async def list_documents(
    skip: int = 0,
    limit: int = 1000,
    provider: Optional[str] = None,
    category: Optional[str] = None,
    doc_status: Optional[DocumentStatus] = None,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """
    获取文档列表

    - **skip**: 跳过的文档数量
    - **limit**: 返回的文档数量限制
    - **provider**: 按提供商过滤
    - **category**: 按分类过滤
    - **status**: 按状态过滤
    """
    try:
        # 构建查询
        query = db.query(Document)
        
        # 应用过滤条件
        if provider:
            query = query.filter(Document.provider == provider)
        if category:
            query = query.filter(Document.category == category)
        if doc_status:
            query = query.filter(Document.status == doc_status)
        
        # 应用分页
        total = query.count()
        documents = query.offset(skip).limit(limit).all()
        
        # 转换为响应模型
        document_responses = [DocumentResponse.from_orm(doc) for doc in documents]
        
        return {
            "documents": document_responses,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}",
        ) from e


@router.post("/documents/upload", summary="上传文档")
async def upload_document(
    file: UploadFile = File(...),
    provider: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    relative_path: Optional[str] = Form(None),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """
    上传新文档到知识库

    - **file**: 要上传的Markdown文件
    - **provider**: 云服务商 (腾讯云、阿里云、火山云、华为云、AWS、Azure、GCP) - 必需
    - **category**: 产品分类 (负载均衡、私有网络、弹性IP、NAT网关、专线、云联网、VPN) - 必需
    - **title**: 文档标题（可选）
    - **relative_path**: 文件的相对路径（用于保留文件夹结构，可选）
    
    文档将按照 /云厂商/产品分类/[相对路径]/ 的目录结构保存
    """
    try:
        # 支持的文件格式
        supported_extensions = ['.md', '.markdown', '.doc', '.docx', '.pdf', '.txt', '.xlsx', '.xls', '.pptx', '.ppt']
        
        # 检查文件类型
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No filename provided",
            )
        
        file_ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
        if f'.{file_ext}' not in supported_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format. Supported formats: {', '.join(supported_extensions)}",
            )

        # 验证必需参数
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provider is required"
            )
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category is required"
            )

        # 创建目录结构: /云厂商/产品分类/[相对路径]/
        base_dir = Path(settings.DOCUMENTS_PATH)
        provider_dir = base_dir / provider
        category_dir = provider_dir / category
        
        # 如果提供了相对路径，则保留文件夹结构
        if relative_path:
            # 清理相对路径，移除开头的斜杠和当前目录标记
            clean_path = relative_path.strip('/').strip()
            if clean_path:
                # 提取目录部分（不包括文件名）
                path_parts = Path(clean_path).parent
                if path_parts and str(path_parts) != '.':
                    category_dir = category_dir / path_parts
        
        # 保存文件到对应目录
        file_path = category_dir / file.filename
        
        # 确保目录存在（在文件路径的父目录上调用）
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 处理文档
        processed_doc = document_processor.process_file(str(file_path))
        
        # 添加元数据
        if provider:
            processed_doc['provider'] = provider
        if category:
            processed_doc['category'] = category
        if title:
            processed_doc['title'] = title
        elif not processed_doc.get('title'):
            # 如果没有提供标题，使用文件名（去掉扩展名）
            processed_doc['title'] = file.filename.rsplit('.', 1)[0]

        # 保存到数据库
        # 从metadata中提取必要字段
        metadata = processed_doc.get('metadata', {})
        
        # 准备标签
        tags_value = None
        if 'tags' in metadata:
            tags_str = metadata.get('tags', '')
            if isinstance(tags_str, str) and tags_str:
                tags_value = tags_str.split(',')
            elif isinstance(tags_str, list):
                tags_value = tags_str
        
        # 生成文档标题（优先使用传入的title，否则使用文件名）
        document_title = title if title else file.filename
        if document_title and '.' in document_title:
            # 如果标题包含扩展名，移除扩展名
            document_title = document_title.rsplit('.', 1)[0]
        
        # 生成唯一的文件名（包含相对路径以避免冲突）
        # 使用完整的文件路径作为唯一标识，确保不同目录下的同名文件不会冲突
        unique_filename = file.filename
        if relative_path:
            clean_relative_path = relative_path.strip('/').strip()
            if clean_relative_path:
                # 使用相对路径作为唯一文件名（替换斜杠为下划线）
                unique_filename = clean_relative_path.replace('/', '_')
        
        # 检查是否已存在相同的文件路径（用 file_path 作为唯一标识）
        existing_doc = db.query(Document).filter(Document.file_path == str(file_path)).first()
        if existing_doc:
            # 如果文件已存在，更新而不是创建新记录
            existing_doc.title = document_title
            existing_doc.content = processed_doc.get('content')
            existing_doc.content_hash = processed_doc.get('content_hash')
            existing_doc.source_url = metadata.get('source_url')
            existing_doc.provider = processed_doc.get('provider')
            existing_doc.category = processed_doc.get('category')
            existing_doc.tags = tags_value
            existing_doc.doc_metadata = metadata
            existing_doc.status = DocumentStatus.PROCESSED
            existing_doc.file_size = processed_doc.get('file_size', 0)
            existing_doc.word_count = int(metadata.get('word_count', 0)) if metadata.get('word_count') else None
            existing_doc.vector_indexed = False
            existing_doc.search_indexed = False
            document = existing_doc
        else:
            # 检查是否存在相同文件名的记录（避免唯一性冲突）
            existing_by_filename = db.query(Document).filter(Document.filename == unique_filename).first()
            if existing_by_filename:
                # 如果存在同名文件，在文件名后添加文件路径哈希来确保唯一性
                import hashlib
                path_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
                unique_filename = f"{unique_filename}_{path_hash}"
            
            # 创建新文档记录
            document = Document(
                title=document_title,
                filename=unique_filename,
                file_path=str(file_path),
                content=processed_doc.get('content'),
                content_hash=processed_doc.get('content_hash'),
                source_url=metadata.get('source_url'),
                provider=processed_doc.get('provider'),
                category=processed_doc.get('category'),
                tags=tags_value,
                doc_metadata=metadata,  # 保存完整的元数据
                status=DocumentStatus.PROCESSED,
                file_size=processed_doc.get('file_size', 0),
                word_count=int(metadata.get('word_count', 0)) if metadata.get('word_count') else None,
                vector_indexed=False,
                search_indexed=False,
            )
            db.add(document)
        
        db.commit()
        db.refresh(document)
        
        # 创建索引
        try:
            # 准备向量存储的元数据（直接使用数据库中已保存的值）
            vector_metadata = {
                'title': document.title,
                'filename': document.filename,
                'provider': document.provider or '',
                'category': document.category or '',
                'source_url': document.source_url or '',
            }
            
            logger.info(f"准备索引文档 {document.id}, 提供商: {document.provider}, 分类: {document.category}")
            
            # 添加到向量存储（同时支持语义搜索）
            vector_store = get_vector_store()
            vector_success = vector_store.add_document(
                document_id=document.id,
                chunks=processed_doc.get('chunks', []),
                metadata=vector_metadata,
            )
            
            # 更新索引状态
            # 搜索基于向量存储，因此两个索引状态一致
            if vector_success:
                document.vector_indexed = True
                document.search_indexed = True
                db.commit()
                db.refresh(document)
            else:
                # 索引创建失败，删除文档并抛出异常
                db.delete(document)
                db.commit()
                
                # 删除文件
                if file_path and file_path.exists():
                    file_path.unlink()
                
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create index for document. Please check if the vector store is properly initialized."
                )
            
        except HTTPException:
            raise
        except Exception as index_error:
            # 索引创建失败，删除文档并抛出异常
            logger.error(f"Failed to create index for document {document.id}: {str(index_error)}")
            
            # 回滚数据库
            db.delete(document)
            db.commit()
            
            # 删除文件
            if file_path and file_path.exists():
                file_path.unlink()
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create index: {str(index_error)}"
            )

        return {
            "message": f"Document {file.filename} uploaded successfully",
            "filename": file.filename,
            "document_id": str(document.id),
            "title": document.title,
            "provider": document.provider or '',
            "category": document.category or '',
            "size": str(document.file_size or 0),
            "word_count": str(document.word_count or 0),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(e)}"
        )


@router.post("/reindex", summary="重建索引")
async def reindex_documents() -> dict[str, str]:
    """
    重新构建所有文档的搜索索引

    这个操作会重新处理所有文档并更新向量索引和搜索索引
    """
    try:
        # 重置向量存储
        vector_store = get_vector_store()
        vector_store.reset_collection()

        # 处理文档目录中的所有文件
        documents_path = Path(settings.DOCUMENTS_PATH)
        if not documents_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Documents directory not found"
            )

        # 批量处理文档
        processed_docs = document_processor.batch_process_directory(str(documents_path), "*.md")

        indexed_count = 0
        failed_count = 0

        # 重建索引
        for i, doc_data in enumerate(processed_docs):
            document_id = i + 1  # 临时ID

            try:
                # 添加到向量存储
                vector_store = get_vector_store()
                vector_success = vector_store.add_document(
                    document_id=document_id,
                    chunks=doc_data['chunks'],
                    metadata=doc_data.get('metadata', {}),
                )

                # 添加到搜索索引
                search_engine = get_search_engine()
                search_success = search_engine.index_document(
                    document_id=document_id, document_data=doc_data
                )

                if vector_success and search_success:
                    indexed_count += 1
                else:
                    failed_count += 1

            except Exception as e:
                failed_count += 1
                print(f"Failed to index document {doc_data.get('filename', 'unknown')}: {str(e)}")

        return {
            "message": "Reindexing completed",
            "total_documents": str(len(processed_docs)),
            "indexed_successfully": str(indexed_count),
            "failed": str(failed_count),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Reindexing failed: {str(e)}"
        )


@router.delete("/documents/{document_id}", summary="删除文档")
async def delete_document(
    document_id: int, db: Session = Depends(get_db)
) -> dict[str, str]:
    """
    删除指定文档

    - **document_id**: 要删除的文档ID
    """
    try:
        # 先从数据库获取文档信息
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )
        
        # 保存文件信息用于返回
        filename = document.filename
        file_path = document.file_path
        
        # 从向量存储中删除
        vector_store = get_vector_store()
        vector_store.delete_document(document_id)

        # 从数据库中删除
        db.delete(document)
        db.commit()
        
        # 删除实际文件
        if file_path:
            file_path_obj = Path(file_path)
            if file_path_obj.exists() and file_path_obj.is_file():
                try:
                    file_path_obj.unlink()
                except Exception as e:
                    # 文件删除失败不影响整体删除操作，只记录警告
                    print(f"Warning: Failed to delete file {file_path}: {str(e)}")

        return {"message": f"Document {document_id} deleted successfully", "filename": filename}

    except HTTPException:
        # 直接传递HTTP异常（如404）
        raise
    except Exception as e:
        # 只包装非HTTP异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )


@router.get("/health", summary="系统健康检查")
async def health_check() -> dict[str, Any]:
    """
    检查系统各组件的健康状态

    返回数据库、向量存储、搜索引擎等组件的状态
    """
    try:
        health_service = get_health_service()
        return health_service.get_health_status()

    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@router.get("/metrics", summary="获取系统指标")
async def get_metrics() -> dict[str, Any]:
    """
    获取系统运行指标

    返回文档统计、搜索性能、系统资源使用等指标
    """
    try:
        # 获取向量存储统计
        vector_store = get_vector_store()
        vector_stats = vector_store.get_collection_stats()

        # 获取文档统计
        documents_path = Path(settings.DOCUMENTS_PATH)
        file_count = 0
        total_size = 0

        if documents_path.exists():
            md_files = list(documents_path.glob("*.md"))
            file_count = len(md_files)
            total_size = sum(f.stat().st_size for f in md_files)

        metrics = {
            "documents": {
                "total_files": file_count,
                "total_size_bytes": total_size,
                "indexed_chunks": vector_stats.get("total_chunks", 0),
            },
            "providers": vector_stats.get("providers", []),
            "categories": vector_stats.get("categories", []),
            "embedding_model": vector_stats.get("embedding_model", ""),
            "system": {
                "documents_path": str(documents_path),
                "vector_store_path": settings.CHROMA_PERSIST_DIRECTORY,
            },
        }

        return metrics

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics: {str(e)}",
        )
