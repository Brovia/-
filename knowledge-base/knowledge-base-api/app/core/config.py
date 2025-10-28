"""
应用配置管理
"""

from typing import Any, Optional, Union


class Settings:
    """应用配置类"""

    # 应用基础配置
    APP_NAME: str = "Knowledge Base API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_STR: str = "/api/v1"

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/app.db"

    # 向量数据库配置
    CHROMA_PERSIST_DIRECTORY: str = "./data/vectors"
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000

    # 文件配置
    DOCUMENTS_PATH: str = "./data/documents"
    PROCESSED_PATH: str = "./data/processed"

    # 嵌入模型配置
    EMBEDDING_MODEL: str = "BAAI/bge-small-zh"
    
    # 文档处理配置
    DOCUMENT_CHUNK_SIZE: int = 1000       #文本块大小（默认：1000字符）
    DOCUMENT_CHUNK_OVERLAP: int = 200     #文本块重叠大小（默认：200字符）
    DOCUMENT_SEPARATORS: list[str] = ["\n\n", "\n", "。", "！", "？", "；", " ", ""] #文本分割符列表

    # 监控配置
    PROMETHEUS_PORT: int = 8001

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "JSON"

    # 安全配置
    ALLOWED_HOSTS: list[str] = ["*"]
    CORS_ORIGINS: list[str] = ["*"]
    API_RATE_LIMIT: int = 100
    
    # A2A搜索配置
    # 默认返回结果数量 (1-50)
    A2A_DEFAULT_LIMIT: int = 5
    
    # 默认最小相似度阈值 (0.0-1.0)
    # 0.0: 返回所有结果
    # 0.1-0.3: 宽松过滤，适合全面搜索
    # 0.3-0.5: 中等过滤，平衡质量和数量
    # 0.5-0.7: 严格过滤，高质量结果
    # 0.7-1.0: 极严格过滤，只返回最相关结果
    A2A_DEFAULT_MIN_SCORE: float = 0.3
    
    # 最大返回结果数量限制
    A2A_MAX_LIMIT: int = 50
    
    # 最大查询长度限制
    A2A_MAX_QUERY_LENGTH: int = 500

    @classmethod
    def assemble_cors_origins(cls, v: Union[str, list[str]]) -> list[str]:
        """处理CORS_ORIGINS配置"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        elif isinstance(v, str):
            return [v]
        raise ValueError(v)


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取应用配置"""
    return settings
