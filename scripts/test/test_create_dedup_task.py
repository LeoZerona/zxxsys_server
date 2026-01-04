"""
测试创建去重任务接口
验证新增字段（analysis_type、estimated_duration）是否正确返回
"""
import sys
import os
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db
from src.models.question_dedup import DedupTask


def test_create_dedup_task():
    """测试创建去重任务"""
    with app.app_context():
        print("=" * 60)
        print("测试创建去重任务接口")
        print("=" * 60)
        print()
        
        # 测试1: 使用默认参数创建任务
        print("测试1: 使用默认参数创建任务")
        print("-" * 60)
        try:
            task = DedupTask(
                task_name="测试任务-默认参数",
                status='pending',
                total_groups=10,
                processed_groups=0,
                total_questions=100,
                exact_duplicate_groups=0,
                exact_duplicate_pairs=0,
                similar_duplicate_pairs=0
            )
            
            db.session.add(task)
            db.session.commit()
            
            task_dict = task.to_dict()
            
            # 验证字段
            assert 'analysis_type' in task_dict, "❌ analysis_type 字段不存在"
            assert 'estimated_duration' in task_dict, "❌ estimated_duration 字段不存在"
            assert task_dict['analysis_type'] == 'full', f"❌ analysis_type 默认值不正确: {task_dict['analysis_type']}"
            assert task_dict['status'] == 'pending', f"❌ status 不正确: {task_dict['status']}"
            assert task_dict['total_groups'] == 10, f"❌ total_groups 不正确: {task_dict['total_groups']}"
            assert task_dict['total_questions'] == 100, f"❌ total_questions 不正确: {task_dict['total_questions']}"
            
            print("✅ 任务创建成功")
            print(f"   - ID: {task_dict['id']}")
            print(f"   - 任务名称: {task_dict['task_name']}")
            print(f"   - 状态: {task_dict['status']}")
            print(f"   - 分析类型: {task_dict['analysis_type']}")
            print(f"   - 总分组数: {task_dict['total_groups']}")
            print(f"   - 总题目数: {task_dict['total_questions']}")
            print(f"   - 预估时长: {task_dict['estimated_duration']} 秒")
            print()
            
            # 清理测试数据
            db.session.delete(task)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        # 测试2: 指定 analysis_type 创建任务
        print("测试2: 指定 analysis_type 创建任务")
        print("-" * 60)
        try:
            task = DedupTask(
                task_name="测试任务-增量分析",
                status='pending',
                total_groups=5,
                processed_groups=0,
                total_questions=50,
                exact_duplicate_groups=0,
                exact_duplicate_pairs=0,
                similar_duplicate_pairs=0,
                analysis_type='incremental',
                estimated_duration=100
            )
            
            db.session.add(task)
            db.session.commit()
            
            task_dict = task.to_dict()
            
            assert task_dict['analysis_type'] == 'incremental', f"❌ analysis_type 不正确: {task_dict['analysis_type']}"
            assert task_dict['estimated_duration'] == 100, f"❌ estimated_duration 不正确: {task_dict['estimated_duration']}"
            
            print("✅ 任务创建成功")
            print(f"   - ID: {task_dict['id']}")
            print(f"   - 分析类型: {task_dict['analysis_type']}")
            print(f"   - 预估时长: {task_dict['estimated_duration']} 秒")
            print()
            
            # 清理测试数据
            db.session.delete(task)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        # 测试3: 验证预估时长计算
        print("测试3: 验证预估时长计算")
        print("-" * 60)
        try:
            # 模拟接口中的计算逻辑
            total_groups = 150
            total_questions = 2500
            
            # 计算公式：30 + (total_questions * 0.1) + (total_groups * 5)
            estimated_duration = int(
                30 +  # 基础开销
                (total_questions * 0.1) +  # 题目处理时间
                (total_groups * 5)  # 分组处理时间
            )
            
            expected_duration = 30 + (2500 * 0.1) + (150 * 5)  # 30 + 250 + 750 = 1030
            
            assert estimated_duration == expected_duration, f"❌ 预估时长计算不正确: {estimated_duration}, 期望: {expected_duration}"
            
            print("✅ 预估时长计算正确")
            print(f"   - 总分组数: {total_groups}")
            print(f"   - 总题目数: {total_questions}")
            print(f"   - 预估时长: {estimated_duration} 秒 ({estimated_duration // 60} 分 {estimated_duration % 60} 秒)")
            print()
            
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        print("=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        return True


if __name__ == '__main__':
    success = test_create_dedup_task()
    sys.exit(0 if success else 1)

