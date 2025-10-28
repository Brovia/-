#!/usr/bin/env python3
"""
知识库API开发环境启动脚本
使用模块化架构启动应用，支持热重载
"""

# 修复 uvicorn 元数据问题
import importlib.metadata
import importlib_metadata

# 保存原始版本函数
_original_version = importlib.metadata.version
_original_version_metadata = importlib_metadata.version

# 临时修复：设置 uvicorn 版本
def patched_version(package_name):
    if package_name == "uvicorn":
        return "0.37.0"
    return _original_version(package_name)

importlib.metadata.version = patched_version
importlib_metadata.version = patched_version

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",  # 使用导入字符串以启用reload
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发环境启用热重载
        log_level="info",
        reload_dirs=["app"]  # 只监听app目录的变化
    )
