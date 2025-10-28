#!/usr/bin/env python3
"""
为现有文档创建缺失的向量和搜索索引
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import get_db_context
from app.models.document import Document
from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStore


def fix_document_indices():
    """为缺失索引的文档创建索引"""
    print("🔧 开始修复文档索引...")
    print("=" * 60)
    
    try:
        # 初始化服务
        print("📦 初始化服务...")
        document_processor = DocumentProcessor()
        vector_store = VectorStore()
        
        with get_db_context() as db:
            # 查询所有未索引的文档
            unindexed_docs = db.query(Document).filter(
                (Document.vector_indexed == False) | (Document.search_indexed == False)
            ).all()
            
            if not unindexed_docs:
                print("✅ 所有文档都已经建立索引！")
                return True
            
            print(f"\n📊 找到 {len(unindexed_docs)} 个需要建立索引的文档")
            print()
            
            success_count = 0
            failed_count = 0
            
            for doc in unindexed_docs:
                print(f"📄 处理文档 {doc.id}: {doc.title}")
                print(f"   文件: {doc.filename}")
                print(f"   向量索引: {'✅' if doc.vector_indexed else '❌'}")
                print(f"   搜索索引: {'✅' if doc.search_indexed else '❌'}")
                
                try:
                    # 检查文件是否存在
                    file_path = Path(doc.file_path)
                    if not file_path.exists():
                        print(f"   ⚠️  文件不存在: {doc.file_path}")
                        failed_count += 1
                        continue
                    
                    # 重新处理文档
                    processed_doc = document_processor.process_file(str(file_path))
                    metadata = processed_doc.get('metadata', {})
                    
                    # 创建向量索引（同时支持搜索功能）
                    if not doc.vector_indexed or not doc.search_indexed:
                        print("   🔄 创建向量索引（包含搜索功能）...")
                        vector_success = vector_store.add_document(
                            document_id=doc.id,
                            chunks=processed_doc.get('chunks', []),
                            metadata=metadata,
                        )
                        if vector_success:
                            doc.vector_indexed = True
                            doc.search_indexed = True
                            print("   ✅ 向量和搜索索引创建成功")
                        else:
                            print("   ❌ 索引创建失败")
                    
                    # 提交更改
                    db.commit()
                    
                    if doc.vector_indexed and doc.search_indexed:
                        success_count += 1
                        print("   ✅ 文档索引完成")
                    else:
                        failed_count += 1
                        print("   ⚠️  部分索引创建失败")
                    
                except Exception as e:
                    print(f"   ❌ 处理失败: {str(e)}")
                    failed_count += 1
                    db.rollback()
                
                print()
            
            # 显示最终统计
            print("=" * 60)
            print(f"📈 索引修复完成！")
            print(f"   成功: {success_count} 个文档")
            print(f"   失败: {failed_count} 个文档")
            
            # 显示当前索引状态
            total_docs = db.query(Document).count()
            vector_indexed = db.query(Document).filter(Document.vector_indexed == True).count()
            search_indexed = db.query(Document).filter(Document.search_indexed == True).count()
            
            print(f"\n📊 当前索引状态:")
            print(f"   总文档数: {total_docs}")
            print(f"   向量索引: {vector_indexed}/{total_docs} ({vector_indexed*100//total_docs if total_docs > 0 else 0}%)")
            print(f"   搜索索引: {search_indexed}/{total_docs} ({search_indexed*100//total_docs if total_docs > 0 else 0}%)")
            
            return failed_count == 0
            
    except Exception as e:
        print(f"❌ 修复索引失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("🚀 文档索引修复工具")
    print()
    
    if fix_document_indices():
        print("\n✅ 索引修复完成!")
        sys.exit(0)
    else:
        print("\n⚠️  索引修复完成，但有部分文档失败")
        sys.exit(1)


if __name__ == "__main__":
    main()

