#!/usr/bin/env python3
"""
清除数据库和向量数据库中的所有内容
"""

import os
import shutil
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def clear_sqlite_database():
    """清除SQLite数据库"""
    db_path = Path("./data/app.db")
    
    if db_path.exists():
        try:
            os.remove(db_path)
            print(f"✅ 已删除SQLite数据库: {db_path}")
        except Exception as e:
            print(f"❌ 删除SQLite数据库失败: {e}")
    else:
        print(f"ℹ️  SQLite数据库不存在: {db_path}")


def clear_vector_database():
    """清除ChromaDB向量数据库"""
    vectors_path = Path("./data/vectors")
    
    if vectors_path.exists():
        try:
            # 删除所有向量数据
            for item in vectors_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                    print(f"✅ 已删除向量目录: {item.name}")
                else:
                    os.remove(item)
                    print(f"✅ 已删除向量文件: {item.name}")
            print(f"✅ 已清空向量数据库目录: {vectors_path}")
        except Exception as e:
            print(f"❌ 清除向量数据库失败: {e}")
    else:
        print(f"ℹ️  向量数据库目录不存在: {vectors_path}")


def clear_documents():
    """清除文档存储"""
    documents_path = Path("./data/documents")
    processed_path = Path("./data/processed")
    
    # 清除原始文档
    if documents_path.exists():
        try:
            for item in documents_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    os.remove(item)
            print(f"✅ 已清空文档目录: {documents_path}")
        except Exception as e:
            print(f"❌ 清除文档目录失败: {e}")
    else:
        print(f"ℹ️  文档目录不存在: {documents_path}")
    
    # 清除处理过的文档
    if processed_path.exists():
        try:
            for item in processed_path.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    os.remove(item)
            print(f"✅ 已清空处理文档目录: {processed_path}")
        except Exception as e:
            print(f"❌ 清除处理文档目录失败: {e}")
    else:
        print(f"ℹ️  处理文档目录不存在: {processed_path}")


def main():
    """主函数"""
    print("=" * 60)
    print("开始清除数据库和向量数据库...")
    print("=" * 60)
    
    # 确认操作
    response = input("\n⚠️  警告: 此操作将删除所有数据，是否继续？(yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("❌ 操作已取消")
        return
    
    print("\n开始清除数据...\n")
    
    # 切换到项目根目录
    os.chdir(Path(__file__).parent.parent)
    
    # 清除SQLite数据库
    print("\n[1/3] 清除SQLite数据库...")
    clear_sqlite_database()
    
    # 清除向量数据库
    print("\n[2/3] 清除ChromaDB向量数据库...")
    clear_vector_database()
    
    # 清除文档存储
    print("\n[3/3] 清除文档存储...")
    clear_documents()
    
    print("\n" + "=" * 60)
    print("✅ 所有数据已清除完成！")
    print("=" * 60)
    print("\n提示: 您可以运行以下命令重新初始化数据库:")
    print("  python scripts/init_db.py")
    print()


if __name__ == "__main__":
    main()

