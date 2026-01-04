"""
测试创建去重任务API接口
通过HTTP请求测试接口功能
"""
import sys
import os
import json
import requests
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# API基础URL
BASE_URL = 'http://localhost:5000'


def test_create_task_default():
    """测试1: 使用默认参数创建任务"""
    print("=" * 60)
    print("测试1: 使用默认参数创建任务")
    print("-" * 60)
    
    url = f"{BASE_URL}/api/dedup/tasks"
    data = {
        "task_name": f"测试任务-默认参数-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        
        print(f"请求URL: {url}")
        print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        print(f"响应状态码: {response.status_code}")
        
        result = response.json()
        print(f"响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 201 and result.get('success'):
            task_data = result.get('data', {})
            
            # 验证字段
            assert 'id' in task_data, "❌ id 字段不存在"
            assert 'status' in task_data, "❌ status 字段不存在"
            assert task_data['status'] == 'pending', f"❌ status 不正确: {task_data['status']}"
            assert 'analysis_type' in task_data, "❌ analysis_type 字段不存在"
            assert task_data['analysis_type'] == 'full', f"❌ analysis_type 默认值不正确: {task_data['analysis_type']}"
            assert 'total_groups' in task_data, "❌ total_groups 字段不存在"
            assert 'total_questions' in task_data, "❌ total_questions 字段不存在"
            assert 'estimated_duration' in task_data, "❌ estimated_duration 字段不存在"
            
            print()
            print("✅ 测试通过")
            print(f"   - 任务ID: {task_data['id']}")
            print(f"   - 任务名称: {task_data['task_name']}")
            print(f"   - 状态: {task_data['status']}")
            print(f"   - 分析类型: {task_data['analysis_type']}")
            print(f"   - 总分组数: {task_data['total_groups']}")
            print(f"   - 总题目数: {task_data['total_questions']}")
            print(f"   - 预估时长: {task_data['estimated_duration']} 秒 ({task_data['estimated_duration'] // 60} 分 {task_data['estimated_duration'] % 60} 秒)")
            
            return task_data['id']
        else:
            print(f"❌ 测试失败: {result.get('message', '未知错误')}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 请确保Flask应用正在运行 (python app.py)")
        return None
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_create_task_with_analysis_type():
    """测试2: 指定分析类型创建任务"""
    print()
    print("=" * 60)
    print("测试2: 指定分析类型创建任务")
    print("-" * 60)
    
    url = f"{BASE_URL}/api/dedup/tasks"
    data = {
        "task_name": f"测试任务-增量分析-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "analysis_type": "incremental",
        "config": {
            "similarity_threshold": 0.85
        }
    }
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        
        print(f"请求URL: {url}")
        print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        print(f"响应状态码: {response.status_code}")
        
        result = response.json()
        print(f"响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 201 and result.get('success'):
            task_data = result.get('data', {})
            
            assert task_data['analysis_type'] == 'incremental', f"❌ analysis_type 不正确: {task_data['analysis_type']}"
            assert task_data['config']['similarity_threshold'] == 0.85, f"❌ config 不正确"
            
            print()
            print("✅ 测试通过")
            print(f"   - 任务ID: {task_data['id']}")
            print(f"   - 分析类型: {task_data['analysis_type']}")
            print(f"   - 相似度阈值: {task_data['config']['similarity_threshold']}")
            
            return task_data['id']
        else:
            print(f"❌ 测试失败: {result.get('message', '未知错误')}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 请确保Flask应用正在运行 (python app.py)")
        return None
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_create_task_invalid_analysis_type():
    """测试3: 无效的分析类型"""
    print()
    print("=" * 60)
    print("测试3: 无效的分析类型（应该返回错误）")
    print("-" * 60)
    
    url = f"{BASE_URL}/api/dedup/tasks"
    data = {
        "task_name": f"测试任务-无效类型-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "analysis_type": "invalid_type"
    }
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'})
        
        print(f"请求URL: {url}")
        print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        print(f"响应状态码: {response.status_code}")
        
        result = response.json()
        print(f"响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 400 and not result.get('success'):
            print()
            print("✅ 测试通过（正确返回错误）")
            print(f"   - 错误信息: {result.get('message')}")
            return True
        else:
            print("❌ 测试失败: 应该返回400错误")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 请确保Flask应用正在运行 (python app.py)")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_get_task_detail(task_id):
    """测试4: 获取任务详情"""
    if not task_id:
        print()
        print("=" * 60)
        print("测试4: 获取任务详情（跳过，无任务ID）")
        return False
    
    print()
    print("=" * 60)
    print(f"测试4: 获取任务详情 (ID: {task_id})")
    print("-" * 60)
    
    url = f"{BASE_URL}/api/dedup/tasks/{task_id}"
    
    try:
        response = requests.get(url)
        
        print(f"请求URL: {url}")
        print(f"响应状态码: {response.status_code}")
        
        result = response.json()
        print(f"响应数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 200 and result.get('success'):
            task_data = result.get('data', {})
            
            assert 'analysis_type' in task_data, "❌ analysis_type 字段不存在"
            assert 'estimated_duration' in task_data, "❌ estimated_duration 字段不存在"
            
            print()
            print("✅ 测试通过")
            print(f"   - 任务ID: {task_data['id']}")
            print(f"   - 分析类型: {task_data['analysis_type']}")
            print(f"   - 预估时长: {task_data['estimated_duration']} 秒")
            
            return True
        else:
            print(f"❌ 测试失败: {result.get('message', '未知错误')}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 请确保Flask应用正在运行 (python app.py)")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("=" * 60)
    print("创建去重任务API接口测试")
    print("=" * 60)
    print()
    print("⚠️  请确保Flask应用正在运行:")
    print("   python app.py")
    print()
    
    results = []
    
    # 测试1: 默认参数
    task_id_1 = test_create_task_default()
    results.append(('测试1: 默认参数', task_id_1 is not None))
    
    # 测试2: 指定分析类型
    task_id_2 = test_create_task_with_analysis_type()
    results.append(('测试2: 指定分析类型', task_id_2 is not None))
    
    # 测试3: 无效的分析类型
    result_3 = test_create_task_invalid_analysis_type()
    results.append(('测试3: 无效的分析类型', result_3))
    
    # 测试4: 获取任务详情
    result_4 = test_get_task_detail(task_id_1)
    results.append(('测试4: 获取任务详情', result_4))
    
    # 汇总结果
    print()
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print()
    print(f"总计: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print()
        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        return True
    else:
        print()
        print("=" * 60)
        print("❌ 部分测试失败")
        print("=" * 60)
        return False


if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)

