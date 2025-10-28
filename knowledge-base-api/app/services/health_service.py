"""
健康检查服务
"""

import time
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.services.vector_store import VectorStore


class HealthService:
    """系统健康检查聚合服务"""

    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.settings = get_settings()

    def get_health_status(self) -> dict[str, Any]:
        """返回统一健康状态结构"""
        vector_status = self.vector_store is not None
        model_status = (
            getattr(self.vector_store, "embedding_model", None) is not None
            if self.vector_store
            else False
        )

        # 搜索引擎状态（使用 ChromaDB + FlagEmbedding）
        search_engine_status = "healthy" if vector_status and model_status else "unhealthy"
        search_engine_note = (
            "ChromaDB + FlagEmbedding (BGE)"
            if search_engine_status == "healthy"
            else "Vector store or embedding model unavailable"
        )

        # 文档存储
        documents_path = Path(self.settings.DOCUMENTS_PATH)
        document_storage: dict[str, Any] = {"status": "healthy" if documents_path.exists() else "unhealthy"}
        if documents_path.exists():
            document_storage.update({"files": str(len(list(documents_path.glob("*.md"))))})
        else:
            document_storage.update({"error": "Documents directory not found"})

        return {
            "status": "healthy" if (vector_status and model_status) else "degraded",
            "timestamp": time.time(),
            "components": {
                "vector_store": {"status": "healthy" if vector_status else "unhealthy"},
                "embedding_model": {"status": "healthy" if model_status else "unhealthy"},
                "document_storage": document_storage,
                "search_engine": {"status": search_engine_status, "note": search_engine_note},
            },
        }
