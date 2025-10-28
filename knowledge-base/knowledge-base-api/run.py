#!/usr/bin/env python3
"""
知识库API启动脚本
使用模块化架构启动应用
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # 生产环境建议关闭
        log_level="info"
    )
