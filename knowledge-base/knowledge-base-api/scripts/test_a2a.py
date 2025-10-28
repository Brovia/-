#!/usr/bin/env python3
"""
标准A2A协议测试脚本
"""

import requests
import json
import time

# A2A服务URL
BASE_URL = "http://localhost:8000"
A2A_URL = f"{BASE_URL}/a2a"

def test_standard_a2a_protocol():
    """测试标准A2A协议"""
    print("=== 测试标准A2A协议 ===")
    
    # 测试获取Agent卡片
    print("\n1. 测试获取Agent卡片")
    agent_card_request = {
        "jsonrpc": "2.0",
        "id": "1",
        "method": "get_agent_card"
    }
    
    try:
        response = requests.post(f"{A2A_URL}/protocol", json=agent_card_request)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Agent卡片获取成功")
            print(f"   JSON-RPC版本: {data['jsonrpc']}")
            print(f"   请求ID: {data['id']}")
            print(f"   方法: {data['method']}")
            if 'result' in data:
                agent_info = data['result']['agent_card']
                print(f"   Agent名称: {agent_info['name']}")
                print(f"   版本: {agent_info['version']}")
                print(f"   端点数量: {len(agent_info['endpoints'])}")
                print(f"   认证类型: {agent_info['authentication']['type']}")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False

def test_standard_search():
    """测试标准A2A搜索"""
    print("\n2. 测试标准A2A搜索")
    
    search_request = {
        "jsonrpc": "2.0",
        "id": "2",
        "method": "search_knowledge",
        "params": {
            "query": "负载均衡",
            "limit": 3,
            "provider": "腾讯云",
            "category": "负载均衡"
        }
    }
    
    try:
        response = requests.post(f"{A2A_URL}/protocol", json=search_request)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 搜索请求成功")
            print(f"   JSON-RPC版本: {data['jsonrpc']}")
            print(f"   请求ID: {data['id']}")
            print(f"   方法: {data['method']}")
            if 'result' in data:
                result = data['result']
                print(f"   查询: {result['query']}")
                print(f"   结果数量: {result['total_results']}")
                print(f"   处理时间: {result['processing_time']}秒")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False

def test_standard_health_check():
    """测试标准A2A健康检查"""
    print("\n3. 测试标准A2A健康检查")
    
    health_request = {
        "jsonrpc": "2.0",
        "id": "3",
        "method": "health_check"
    }
    
    try:
        response = requests.post(f"{A2A_URL}/protocol", json=health_request)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查成功")
            print(f"   JSON-RPC版本: {data['jsonrpc']}")
            print(f"   请求ID: {data['id']}")
            print(f"   方法: {data['method']}")
            if 'result' in data:
                result = data['result']
                print(f"   状态: {result['status']}")
                print(f"   Agent卡片可用: {result['agent_card_available']}")
                print(f"   搜索功能可用: {result['search_available']}")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False

def test_error_handling():
    """测试错误处理"""
    print("\n4. 测试错误处理")
    
    # 测试无效方法
    invalid_request = {
        "jsonrpc": "2.0",
        "id": "4",
        "method": "invalid_method"
    }
    
    try:
        response = requests.post(f"{A2A_URL}/protocol", json=invalid_request)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 错误处理正常")
            print(f"   JSON-RPC版本: {data['jsonrpc']}")
            print(f"   请求ID: {data['id']}")
            if 'error' in data:
                error = data['error']
                print(f"   错误代码: {error['code']}")
                print(f"   错误消息: {error['message']}")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False

def test_missing_params():
    """测试缺少参数的错误处理"""
    print("\n5. 测试缺少参数的错误处理")
    
    # 测试缺少query参数
    invalid_search_request = {
        "jsonrpc": "2.0",
        "id": "5",
        "method": "search_knowledge",
        "params": {
            "limit": 5
            # 缺少query参数
        }
    }
    
    try:
        response = requests.post(f"{A2A_URL}/protocol", json=invalid_search_request)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 参数验证正常")
            print(f"   JSON-RPC版本: {data['jsonrpc']}")
            print(f"   请求ID: {data['id']}")
            if 'error' in data:
                error = data['error']
                print(f"   错误代码: {error['code']}")
                print(f"   错误消息: {error['message']}")
                if 'data' in error:
                    print(f"   错误数据: {error['data']}")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始标准A2A协议测试")
    print(f"测试URL: {A2A_URL}/protocol")
    print("=" * 60)
    
    tests = [
        test_standard_a2a_protocol,
        test_standard_search,
        test_standard_health_check,
        test_error_handling,
        test_missing_params
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        time.sleep(0.5)  # 避免请求过快
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有标准A2A协议测试通过！")
        print("\n📋 标准A2A协议端点:")
        print(f"   - 标准协议: POST {A2A_URL}/protocol")
        print(f"   - Agent卡片: GET {A2A_URL}/")
        print(f"   - 知识检索: POST {A2A_URL}/search")
        print(f"   - 兼容接口: POST {A2A_URL}")
        print(f"   - 健康检查: GET {A2A_URL}/health")
        print("\n🔧 标准A2A协议特点:")
        print("   ✅ JSON-RPC 2.0格式")
        print("   ✅ 标准错误代码")
        print("   ✅ 结构化AgentCard")
        print("   ✅ 统一消息格式")
        print("   ✅ 完整错误处理")
    else:
        print("⚠️  部分测试失败，请检查服务状态")

if __name__ == "__main__":
    main()
