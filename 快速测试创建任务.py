"""
快速测试创建去重任务接口
"""
import sys
import os
import json
import requests
from datetime import datetime

# API基础URL
BASE_URL = 'http://localhost:5000'


def format_duration(seconds):
    """格式化时长"""
    if seconds is None:
        return "未计算"
    minutes = seconds // 60
    secs = seconds % 60
    if minutes > 0:
        return f"{minutes}分{secs}秒"
    return f"{secs}秒"


def test_create_task():
    """测试创建任务"""
    print("=" * 60)
    print("快速测试：创建去重任务接口")
    print("=" * 60)
    print()
    print("⚠️  请确保Flask应用正在运行: python app.py")
    print()
    
    # 测试1: 默认参数
    print("测试1: 创建任务（默认参数）")
    print("-" * 60)
    
    url = f"{BASE_URL}/api/dedup/tasks"
    data = {
        "task_name": f"测试任务-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }
    
    try:
        response = requests.post(url, json=data, headers={'Content-Type': 'application/json'}, timeout=10)
        
        if response.status_code == 201:
            result = response.json()
            if result.get('success'):
                task_data = result.get('data', {})
                
                print("✅ 任务创建成功！")
                print()
                print("任务信息：")
                print(f"  - 任务ID: {task_data.get('id')}")
                print(f"  - 任务名称: {task_data.get('task_name')}")
                print(f"  - 状态: {task_data.get('status')}")
                print(f"  - 分析类型: {task_data.get('analysis_type')}")
                print(f"  - 总分组数: {task_data.get('total_groups')}")
                print(f"  - 总题目数: {task_data.get('total_questions')}")
                print(f"  - 预估时长: {format_duration(task_data.get('estimated_duration'))}")
                print()
                
                # 验证字段
                if task_data.get('analysis_type'):
                    print("✅ analysis_type 字段存在")
                else:
                    print("❌ analysis_type 字段不存在")
                
                if task_data.get('estimated_duration') is not None:
                    print("✅ estimated_duration 字段存在")
                else:
                    print("❌ estimated_duration 字段不存在")
                
                if task_data.get('status') == 'pending':
                    print("✅ 任务状态为 pending（待启动）")
                else:
                    print(f"⚠️  任务状态为 {task_data.get('status')}")
                
                print()
                print("=" * 60)
                print("✅ 测试完成！")
                print("=" * 60)
                return True
            else:
                print(f"❌ 创建失败: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败！")
        print()
        print("请确保Flask应用正在运行：")
        print("  python app.py")
        print()
        print("或者检查应用是否运行在正确的端口（默认5000）")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    try:
        success = test_create_task()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)

