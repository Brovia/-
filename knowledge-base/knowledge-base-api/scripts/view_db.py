#!/usr/bin/env python3
"""
查看 SQLite 数据库内容的脚本
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_db_context
from app.models.document import Document
from sqlalchemy import text


def view_database_info():
    """查看数据库基本信息"""
    print("📊 SQLite 数据库信息")
    print("=" * 50)
    
    try:
        with get_db_context() as db:
            # 获取数据库版本
            result = db.execute(text("SELECT sqlite_version()"))
            version = result.scalar()
            print(f"SQLite 版本: {version}")
            
            # 获取数据库文件信息
            result = db.execute(text("PRAGMA database_list"))
            databases = result.fetchall()
            print(f"数据库文件: {databases[0][2] if databases else 'Unknown'}")
            
            # 获取表信息
            result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = result.fetchall()
            print(f"数据表数量: {len(tables)}")
            print(f"数据表列表: {[table[0] for table in tables]}")
            
            print()
            
    except Exception as e:
        print(f"❌ 获取数据库信息失败: {str(e)}")


def view_documents():
    """查看文档数据"""
    print("📄 文档数据")
    print("=" * 50)
    
    try:
        with get_db_context() as db:
            # 获取文档总数
            total_docs = db.query(Document).count()
            print(f"文档总数: {total_docs}")
            
            if total_docs == 0:
                print("📝 数据库中没有文档数据")
                return
            
            # 获取所有文档
            documents = db.query(Document).all()
            
            for i, doc in enumerate(documents, 1):
                print(f"\n📄 文档 {i}:")
                print(f"  ID: {doc.id}")
                print(f"  标题: {doc.title}")
                print(f"  文件名: {doc.filename}")
                print(f"  文件路径: {doc.file_path}")
                print(f"  提供商: {doc.provider}")
                print(f"  分类: {doc.category}")
                print(f"  状态: {doc.status}")
                print(f"  文件大小: {doc.file_size} bytes")
                print(f"  字数: {doc.word_count}")
                print(f"  向量索引: {'✅' if doc.vector_indexed else '❌'}")
                print(f"  搜索索引: {'✅' if doc.search_indexed else '❌'}")
                print(f"  创建时间: {doc.created_at}")
                print(f"  更新时间: {doc.updated_at}")
                if doc.processed_at:
                    print(f"  处理时间: {doc.processed_at}")
                if doc.content:
                    content_preview = doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                    print(f"  内容预览: {content_preview}")
                if doc.tags:
                    print(f"  标签: {doc.tags}")
                if doc.doc_metadata:
                    print(f"  元数据: {doc.doc_metadata}")
                    
    except Exception as e:
        print(f"❌ 查看文档数据失败: {str(e)}")


def view_database_statistics():
    """查看数据库统计信息"""
    print("📈 数据库统计信息")
    print("=" * 50)
    
    try:
        with get_db_context() as db:
            # 按状态统计
            from sqlalchemy import func
            status_stats = db.query(
                Document.status, 
                func.count(Document.id).label('count')
            ).group_by(Document.status).all()
            
            print("📊 按状态统计:")
            for status, count in status_stats:
                print(f"  {status}: {count} 个文档")
            
            # 按提供商统计
            provider_stats = db.query(
                Document.provider, 
                func.count(Document.id).label('count')
            ).group_by(Document.provider).all()
            
            print("\n📊 按提供商统计:")
            for provider, count in provider_stats:
                print(f"  {provider or 'Unknown'}: {count} 个文档")
            
            # 按分类统计
            category_stats = db.query(
                Document.category, 
                func.count(Document.id).label('count')
            ).group_by(Document.category).all()
            
            print("\n📊 按分类统计:")
            for category, count in category_stats:
                print(f"  {category or 'Unknown'}: {count} 个文档")
            
            # 索引状态统计
            vector_indexed = db.query(Document).filter(Document.vector_indexed == True).count()
            search_indexed = db.query(Document).filter(Document.search_indexed == True).count()
            
            print(f"\n📊 索引状态:")
            print(f"  向量索引: {vector_indexed} 个文档")
            print(f"  搜索索引: {search_indexed} 个文档")
            
    except Exception as e:
        print(f"❌ 查看统计信息失败: {str(e)}")


def main():
    """主函数"""
    print("🔍 SQLite 数据库内容查看器")
    print("=" * 60)
    
    view_database_info()
    view_documents()
    view_database_statistics()
    
    print("\n" + "=" * 60)
    print("✅ 数据库内容查看完成")


if __name__ == "__main__":
    main()
