#!/usr/bin/env python3
"""
API测试脚本
"""
import time

import requests


class APITester:
    """API测试器"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def test_health(self):
        """测试健康检查"""
        print("测试健康检查...")
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✓ 健康检查正常")
                return True
            else:
                print(f"✗ 健康检查失败: {response.status_code}")
                return False
        except Exception as e:
            print(f"✗ 健康检查异常: {str(e)}")
            return False

    def get_headers(self):
        """获取请求头"""
        return {}

    def test_search(self):
        """测试搜索功能"""
        print("测试搜索功能...")
        try:
            # 测试查询
            test_queries = ["负载均衡", "阿里云ALB", "腾讯云CLB", "什么是负载均衡"]

            for query in test_queries:
                print(f"  搜索: {query}")

                response = requests.get(
                    f"{self.base_url}/api/v1/knowledge/search",
                    params={"query": query, "search_type": "hybrid", "limit": 5},
                    headers=self.get_headers(),
                )

                if response.status_code == 200:
                    data = response.json()
                    print(f"    ✓ 找到 {data['total']} 个结果")
                    if data['results']:
                        print(f"    最高分: {data['results'][0]['score']:.3f}")
                else:
                    print(f"    ✗ 搜索失败: {response.status_code}")
                    return False

                time.sleep(0.5)  # 避免请求过快

            print("✓ 搜索测试完成")
            return True

        except Exception as e:
            print(f"✗ 搜索测试异常: {str(e)}")
            return False

    def test_qa(self):
        """测试问答功能"""
        print("测试问答功能...")
        try:
            test_questions = [
                "阿里云ALB和腾讯云CLB有什么区别？",
                "负载均衡的主要作用是什么？",
                "什么是应用型负载均衡？",
            ]

            for question in test_questions:
                print(f"  问题: {question}")

                qa_data = {
                    "question": question,
                    "context_limit": 3,
                    "include_sources": True,
                    "temperature": 0.7,
                }

                response = requests.post(
                    f"{self.base_url}/api/v1/knowledge/qa", json=qa_data, headers=self.get_headers()
                )

                if response.status_code == 200:
                    data = response.json()
                    print(f"    ✓ 回答长度: {len(data['answer'])} 字符")
                    print(f"    置信度: {data['confidence']:.3f}")
                    print(f"    来源数量: {len(data['sources'])}")
                else:
                    print(f"    ✗ 问答失败: {response.status_code}")
                    return False

                time.sleep(1)  # 问答可能较慢

            print("✓ 问答测试完成")
            return True

        except Exception as e:
            print(f"✗ 问答测试异常: {str(e)}")
            return False

    def test_recommend(self):
        """测试推荐功能"""
        print("测试推荐功能...")
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/knowledge/recommend",
                params={"query": "负载均衡技术", "limit": 5, "similarity_threshold": 0.3},
                headers=self.get_headers(),
            )

            if response.status_code == 200:
                data = response.json()
                print(f"  ✓ 推荐 {len(data['recommendations'])} 个文档")
                return True
            else:
                print(f"  ✗ 推荐失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"✗ 推荐测试异常: {str(e)}")
            return False

    def test_stats(self):
        """测试统计信息"""
        print("测试统计信息...")
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/knowledge/stats", headers=self.get_headers()
            )

            if response.status_code == 200:
                data = response.json()
                print("  ✓ 获取统计信息成功")
                if 'vector_store' in data:
                    vector_stats = data['vector_store']
                    print(f"    文本块数量: {vector_stats.get('total_chunks', 0)}")
                return True
            else:
                print(f"  ✗ 统计信息获取失败: {response.status_code}")
                return False

        except Exception as e:
            print(f"✗ 统计信息测试异常: {str(e)}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 50)
        print("开始API测试")
        print("=" * 50)

        tests = [
            self.test_health,
            self.test_search,
            self.test_qa,
            self.test_recommend,
            self.test_stats,
        ]

        passed = 0
        total = len(tests)

        for test in tests:
            if test():
                passed += 1
            print()

        print("=" * 50)
        print(f"测试完成: {passed}/{total} 通过")
        if passed == total:
            print("🎉 所有测试通过!")
        else:
            print("⚠️  部分测试失败，请检查服务状态")
        print("=" * 50)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="API测试脚本")
    parser.add_argument("--url", default="http://localhost:8000", help="API服务地址")

    args = parser.parse_args()

    tester = APITester(args.url)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
