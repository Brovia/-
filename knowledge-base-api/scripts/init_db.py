#!/usr/bin/env python3
"""
数据库初始化脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import init_database
from app.core.config import get_settings
# 导入模型以确保表被创建
from app.models import Document


def main():
    """初始化数据库"""
    settings = get_settings()
    print(f"🔧 Initializing database: {settings.DATABASE_URL}")
    
    try:
        init_database()
        print("✅ Database initialization completed successfully!")
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
