#!/usr/bin/env python3
"""
查看向量数据库中的向量数据
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import chromadb
from FlagEmbedding import FlagModel
from app.core.config import get_settings


def view_vectors_simple():
    """简单查看向量数据"""
    print("🔍 向量数据库简单查看")
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
        
        # 获取基本信息
        count = collection.count()
        print(f"📊 向量块总数: {count}")
        
        if count == 0:
            print("📝 向量数据库中没有数据")
            return
        
        # 获取所有数据
        all_data = collection.get(include=['embeddings', 'documents', 'metadatas'])
        
        print(f"📊 数据概览:")
        print(f"  ID数量: {len(all_data['ids'])}")
        print(f"  文档数量: {len(all_data['documents'])}")
        print(f"  元数据数量: {len(all_data['metadatas'])}")
        print(f"  向量数量: {len(all_data['embeddings'])}")
        
        # 显示每个向量块的基本信息
        for i, (id_val, doc, metadata, embedding) in enumerate(zip(
            all_data['ids'], 
            all_data['documents'], 
            all_data['metadatas'],
            all_data['embeddings']
        )):
            print(f"\n🔸 向量块 {i+1}:")
            print(f"  ID: {id_val}")
            print(f"  文档ID: {metadata.get('document_id', 'N/A')}")
            print(f"  块索引: {metadata.get('chunk_index', 'N/A')}")
            print(f"  字数: {metadata.get('word_count', 'N/A')}")
            print(f"  提供商: {metadata.get('provider', 'N/A')}")
            print(f"  分类: {metadata.get('category', 'N/A')}")
            print(f"  内容长度: {len(doc)} 字符")
            print(f"  向量维度: {len(embedding)}")
            print(f"  内容预览: {doc[:100]}{'...' if len(doc) > 100 else ''}")
        
        # 简单的向量统计
        print(f"\n📊 向量统计:")
        all_embeddings = all_data['embeddings']
        if len(all_embeddings) > 0:
            # 收集所有向量值
            all_values = []
            for emb in all_embeddings:
                if emb is not None and len(emb) > 0:  # 确保embedding不为空
                    all_values.extend(emb)
            
            if all_values:
                print(f"  总数值数量: {len(all_values)}")
                print(f"  最小值: {min(all_values):.6f}")
                print(f"  最大值: {max(all_values):.6f}")
                print(f"  均值: {sum(all_values)/len(all_values):.6f}")
                
                # 计算标准差
                mean = sum(all_values)/len(all_values)
                variance = sum((x - mean)**2 for x in all_values) / len(all_values)
                std_dev = variance**0.5
                print(f"  标准差: {std_dev:.6f}")
            else:
                print("  没有有效的向量数据")
        
        print(f"\n{'='*60}")
        print("✅ 向量数据查看完成")
        
    except Exception as e:
        print(f"❌ 查看向量数据失败: {str(e)}")
        import traceback
        traceback.print_exc()


def test_search():
    """测试搜索功能"""
    print("\n🔍 搜索功能测试")
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
        
        # 初始化嵌入模型
        print(f"📦 加载嵌入模型: {settings.EMBEDDING_MODEL}")
        embedding_model = FlagModel(
            settings.EMBEDDING_MODEL, 
            query_instruction_for_retrieval="为这个句子生成表示以用于检索相关文章："
        )
        
        # 测试查询
        test_queries = ["健康检查", "负载均衡", "操作日志"]
        
        for query in test_queries:
            print(f"\n🔍 查询: '{query}'")
            
            # 生成查询向量
            query_embedding = embedding_model.encode([query]).tolist()
            print(f"  向量维度: {len(query_embedding[0])}")
            
            # 执行搜索
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=2,
                include=['metadatas', 'documents', 'distances']
            )
            
            if results['ids'] and results['ids'][0]:
                for i, (id_val, doc, metadata, distance) in enumerate(zip(
                    results['ids'][0],
                    results['documents'][0],
                    results['metadatas'][0],
                    results['distances'][0]
                )):
                    print(f"  {i+1}. 距离: {distance:.4f}")
                    print(f"     ID: {id_val}")
                    print(f"     文档: {metadata.get('document_id', 'N/A')}")
                    print(f"     内容: {doc[:80]}{'...' if len(doc) > 80 else ''}")
            else:
                print("  没有找到相关结果")
        
        print(f"\n{'='*60}")
        print("✅ 搜索功能测试完成")
        
    except Exception as e:
        print(f"❌ 搜索功能测试失败: {str(e)}")


def main():
    """主函数"""
    print("🔍 向量数据库简单查看器")
    print("=" * 80)
    
    # 查看向量数据
    view_vectors_simple()
    
    # 测试搜索功能
    test_search()
    
    print("=" * 80)
    print("✅ 所有操作完成")


if __name__ == "__main__":
    main()
