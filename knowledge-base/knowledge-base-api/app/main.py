"""
主应用入口
"""

import time
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import admin, knowledge, a2a
from app.core.config import get_settings
from app.core.logging import get_logger, log_request, log_error, log_performance

# 获取日志记录器
logger = get_logger("main")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 Starting Knowledge Base API...")

    # 初始化数据目录
    import os
    from pathlib import Path

    os.makedirs(settings.DOCUMENTS_PATH, exist_ok=True)
    os.makedirs(settings.PROCESSED_PATH, exist_ok=True)
    os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)

    # 初始化数据库
    try:
        from app.core.database import init_database
        init_database()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise

    # 初始化向量存储和处理文档
    try:
        from app.services.vector_store import VectorStore
        from app.services.document_processor import DocumentProcessor
        
        start_time = time.time()
        vector_store = VectorStore()
        document_processor = DocumentProcessor()
        
        # 处理文档目录中的所有文件
        documents_path = Path(settings.DOCUMENTS_PATH)
        if documents_path.exists():
            processed_count = 0
            for md_file in documents_path.glob("*.md"):
                try:
                    processed_doc = document_processor.process_file(str(md_file))
                    if processed_doc:
                        # 添加到向量存储
                        vector_store.add_document(
                            document_id=processed_count,
                            chunks=processed_doc["chunks"],
                            metadata=processed_doc["metadata"]
                        )
                        processed_count += 1
                        logger.info(f"✅ Processed: {md_file.name}")
                except Exception as e:
                    logger.error(f"❌ Failed to process {md_file.name}: {str(e)}")
            
            logger.info(f"📚 Processed {processed_count} documents")
            log_performance("document_processing", time.time() - start_time, count=processed_count)
        else:
            logger.warning(f"Documents directory not found: {documents_path}")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize vector store: {str(e)}")

    logger.info("✅ Knowledge Base API started successfully!")

    yield

    # 关闭时执行
    logger.info("Shutting down Knowledge Base API...")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="知识库A2A调用API服务",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加受信任主机中间件
if not settings.DEBUG:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)


# 请求处理时间中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Any) -> Any:
    start_time = time.time()
    
    # 生成请求ID
    request_id = f"{int(start_time * 1000)}"
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 添加响应头
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        # 记录请求日志
        log_request(
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            duration=process_time
        )
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        log_error(e, f"Request {request_id}: {request.method} {request.url}")
        raise


# 全局异常处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    log_error(exc, f"HTTP Exception: {request.method} {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {"code": exc.status_code, "message": exc.detail, "timestamp": time.time()}
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log_error(exc, f"General Exception: {request.method} {request.url}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {"code": 500, "message": "Internal server error", "timestamp": time.time()}
        },
    )


# 根路径
@app.get("/", summary="API根路径")
async def root() -> dict[str, Any]:
    """API根路径，返回基本信息"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "知识库A2A调用API服务",
        "docs_url": "/docs",
        "health_check": "/api/v1/admin/health",
        "a2a_endpoint": "/a2a",
        "a2a_agent_card": "/a2a/",
        "a2a_search": "/a2a/search",
        "a2a_protocol": "/a2a/protocol",
    }


# 健康检查端点（无需认证）
@app.get("/health", summary="健康检查")
async def health() -> dict[str, Any]:
    """简单的健康检查端点"""
    return {"status": "healthy", "timestamp": time.time(), "version": settings.APP_VERSION}


# 注册API路由
app.include_router(knowledge.router, prefix=f"{settings.API_V1_STR}/knowledge", tags=["知识库"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["管理"])
app.include_router(a2a.router, prefix="/a2a", tags=["A2A服务"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG, log_level="info")
