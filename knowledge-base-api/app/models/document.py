"""
文档数据模型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.core.database import Base


class DocumentStatus(str, Enum):
    """文档状态枚举"""

    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Document(Base):
    """文档数据库模型"""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False, index=True)
    filename = Column(String(255), nullable=False, unique=True, index=True)
    file_path = Column(String(1000), nullable=False)
    content = Column(Text, nullable=True)
    content_hash = Column(String(64), nullable=True, index=True)

    # 元数据
    source_url = Column(String(1000), nullable=True)
    provider = Column(String(100), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    tags = Column(JSON, nullable=True)
    doc_metadata = Column(JSON, nullable=True)  # 重命名避免与SQLAlchemy metadata冲突

    # 状态和时间
    status = Column(String(20), default=DocumentStatus.PENDING, index=True)
    file_size = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # 索引相关
    vector_indexed = Column(Boolean, default=False, index=True)
    search_indexed = Column(Boolean, default=False, index=True)


# Pydantic模型用于API
class DocumentBase(BaseModel):
    """文档基础模型"""

    title: str = Field(..., max_length=500)
    filename: str = Field(..., max_length=255)
    file_path: str = Field(..., max_length=1000)
    source_url: Optional[str] = Field(None, max_length=1000)
    provider: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None


class DocumentCreate(DocumentBase):
    """创建文档模型"""

    content: Optional[str] = None


class DocumentUpdate(BaseModel):
    """更新文档模型"""

    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    source_url: Optional[str] = Field(None, max_length=1000)
    provider: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = None
    status: Optional[DocumentStatus] = None


class DocumentResponse(BaseModel):
    """文档响应模型"""

    id: int
    title: str = Field(..., max_length=500)
    filename: str = Field(..., max_length=255)
    file_path: str = Field(..., max_length=1000)
    source_url: Optional[str] = Field(None, max_length=1000)
    provider: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[list[str]] = None
    metadata: Optional[dict[str, Any]] = Field(None, alias='doc_metadata')
    content_hash: Optional[str]
    status: DocumentStatus
    file_size: Optional[int]
    word_count: Optional[int]
    vector_indexed: bool
    search_indexed: bool
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True
        populate_by_name = True


class DocumentSearchResult(BaseModel):
    """文档搜索结果模型"""

    id: int
    title: str
    content: str
    source: str
    score: float
    metadata: Optional[dict[str, Any]] = None


class DocumentChunk(BaseModel):
    """文档块模型"""

    id: str
    document_id: int
    content: str
    chunk_index: int
    start_pos: int
    end_pos: int
    metadata: Optional[dict[str, Any]] = None
