#!/usr/bin/env python3
"""
初始化数据脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import get_settings
from app.services.document_processor import DocumentProcessor
from app.services.search_engine import SearchEngine
from app.services.vector_store import VectorStore

settings = get_settings()


async def main():
    """初始化数据"""
    print("开始初始化知识库数据...")

    # 初始化服务
    document_processor = DocumentProcessor()
    vector_store = VectorStore()
    search_engine = SearchEngine()

    # 检查文档目录
    documents_path = Path(settings.DOCUMENTS_PATH)
    if not documents_path.exists():
        print(f"文档目录不存在: {documents_path}")
        return

    # 查找所有Markdown文件
    md_files = list(documents_path.glob("*.md"))
    if not md_files:
        print("未找到Markdown文件")
        return

    print(f"找到 {len(md_files)} 个Markdown文件")

    # 重置向量存储
    print("重置向量存储...")
    vector_store.reset_collection()

    # 处理每个文档
    processed_count = 0
    failed_count = 0

    for i, file_path in enumerate(md_files):
        try:
            print(f"处理文件 ({i+1}/{len(md_files)}): {file_path.name}")

            # 处理文档
            doc_data = document_processor.process_file(str(file_path))

            # 添加到向量存储
            document_id = i + 1
            vector_success = vector_store.add_document(
                document_id=document_id,
                chunks=doc_data['chunks'],
                metadata=doc_data.get('metadata', {}),
            )

            # 添加到搜索索引
            _ = search_engine.index_document(document_id=document_id, document_data=doc_data)

            if vector_success:
                processed_count += 1
                print(f"  ✓ 成功处理: {len(doc_data['chunks'])} 个文本块")
            else:
                failed_count += 1
                print("  ✗ 处理失败")

        except Exception as e:
            failed_count += 1
            print(f"  ✗ 处理失败: {str(e)}")

    print("\n初始化完成:")
    print(f"  成功处理: {processed_count} 个文档")
    print(f"  处理失败: {failed_count} 个文档")

    # 显示统计信息
    stats = vector_store.get_collection_stats()
    print("\n向量存储统计:")
    print(f"  总文本块数: {stats.get('total_chunks', 0)}")
    print(f"  云服务提供商: {', '.join(stats.get('providers', []))}")
    print(f"  文档分类: {', '.join(stats.get('categories', []))}")


if __name__ == "__main__":
    asyncio.run(main())
