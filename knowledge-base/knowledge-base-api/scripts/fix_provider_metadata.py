#!/usr/bin/env python3
"""
修复向量数据库中错误的提供商元数据
从数据库获取正确的提供商信息并更新向量元数据
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import chromadb
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db_context
from app.models.document import Document


def fix_provider_metadata():
    """修复向量数据库中的提供商元数据"""
    print("🔧 修复向量数据库提供商元数据")
    print("=" * 60)
    
    try:
        settings = get_settings()
        
        # 初始化 ChromaDB 客户端
        client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=chromadb.config.Settings(anonymized_telemetry=False)
        )
        
        # 获取集合
        collection = client.get_collection("knowledge_base")
        
        # 获取所有向量数据
        all_data = collection.get(include=['metadatas'])
        
        if not all_data['metadatas']:
            print("📝 向量数据库中没有数据")
            return
        
        print(f"📊 找到 {len(all_data['metadatas'])} 个向量块")
        
        # 从数据库获取正确的文档信息
        with get_db_context() as db:
            documents = db.query(Document).all()
            doc_info = {doc.id: {'provider': doc.provider, 'category': doc.category} for doc in documents}
        
        print(f"📊 从数据库获取到 {len(doc_info)} 个文档信息")
        
        # 统计需要更新的向量块
        update_count = 0
        for i, metadata in enumerate(all_data['metadatas']):
            doc_id = metadata.get('document_id')
            current_provider = metadata.get('provider', '')
            
            if doc_id in doc_info:
                correct_provider = doc_info[doc_id]['provider']
                correct_category = doc_info[doc_id]['category']
                
                if current_provider != correct_provider:
                    print(f"🔸 向量块 {i+1}: 文档 {doc_id}")
                    print(f"  当前提供商: {current_provider}")
                    print(f"  正确提供商: {correct_provider}")
                    print(f"  正确分类: {correct_category}")
                    update_count += 1
        
        if update_count == 0:
            print("✅ 所有向量块的提供商信息都是正确的")
            return
        
        print(f"\n🔄 需要更新 {update_count} 个向量块")
        
        # 执行更新
        for i, (vector_id, metadata) in enumerate(zip(all_data['ids'], all_data['metadatas'])):
            doc_id = metadata.get('document_id')
            
            if doc_id in doc_info:
                correct_provider = doc_info[doc_id]['provider']
                correct_category = doc_info[doc_id]['category']
                
                # 更新元数据
                updated_metadata = metadata.copy()
                updated_metadata['provider'] = correct_provider
                updated_metadata['category'] = correct_category
                
                # 更新向量块的元数据
                collection.update(
                    ids=[vector_id],
                    metadatas=[updated_metadata]
                )
                
                print(f"✅ 已更新向量块 {i+1}: {vector_id}")
        
        print(f"\n{'='*60}")
        print("✅ 提供商元数据修复完成")
        
    except Exception as e:
        print(f"❌ 修复提供商元数据失败: {str(e)}")


def verify_fix():
    """验证修复结果"""
    print("\n🔍 验证修复结果")
    print("=" * 60)
    
    try:
        settings = get_settings()
        
        # 初始化 ChromaDB 客户端
        client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY,
            settings=chromadb.config.Settings(anonymized_telemetry=False)
        )
        
        # 获取集合
        collection = client.get_collection("knowledge_base")
        
        # 获取所有向量数据
        all_data = collection.get(include=['metadatas'])
        
        # 统计提供商分布
        provider_stats = {}
        for metadata in all_data['metadatas']:
            provider = metadata.get('provider', 'Unknown')
            provider_stats[provider] = provider_stats.get(provider, 0) + 1
        
        print("📊 修复后的提供商分布:")
        for provider, count in provider_stats.items():
            print(f"  {provider}: {count} 个向量块")
        
        print(f"\n{'='*60}")
        print("✅ 验证完成")
        
    except Exception as e:
        print(f"❌ 验证失败: {str(e)}")


def main():
    """主函数"""
    print("🔧 向量数据库提供商元数据修复工具")
    print("=" * 80)
    
    # 修复提供商元数据
    fix_provider_metadata()
    
    # 验证修复结果
    verify_fix()
    
    print("=" * 80)
    print("✅ 所有操作完成")


if __name__ == "__main__":
    main()
