"""
测试题目数据分组功能
用于验证预处理阶段的数据分组是否正确
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db
from src.services.question_service import QuestionService


def test_get_question_groups():
    """测试获取题目分组"""
    with app.app_context():
        print("=" * 60)
        print("预处理阶段：数据分组")
        print("=" * 60)
        
        # 1. 查询所有分组
        print("\n1. 查询所有分组（按 type, subject_id, channel_code）...")
        groups = QuestionService.get_question_groups()
        
        print(f"\n共找到 {len(groups)} 个分组")
        
        # 2. 统计每组数量，识别大组和小组
        print("\n2. 统计每组数量...")
        
        total_questions = sum(group['count'] for group in groups)
        print(f"总题目数：{total_questions}")
        print(f"平均每组题目数：{total_questions / len(groups) if groups else 0:.2f}")
        
        # 找出最大的组和最小的组
        if groups:
            max_group = max(groups, key=lambda x: x['count'])
            min_group = min(groups, key=lambda x: x['count'])
            print(f"\n最大的组：")
            print(f"  - 题型：{max_group['type_name']} ({max_group['type']})")
            print(f"  - 科目：{max_group['subject_name']} (ID: {max_group['subject_id']})")
            print(f"  - 渠道：{max_group['channel_code']}")
            print(f"  - 题目数：{max_group['count']}")
            
            print(f"\n最小的组：")
            print(f"  - 题型：{min_group['type_name']} ({min_group['type']})")
            print(f"  - 科目：{min_group['subject_name']} (ID: {min_group['subject_id']})")
            print(f"  - 渠道：{min_group['channel_code']}")
            print(f"  - 题目数：{min_group['count']}")
        
        # 3. 生成分组列表（前10个分组作为示例）
        print("\n3. 生成分组列表（显示前10个分组）：")
        print("-" * 60)
        print(f"{'序号':<6} {'题型':<12} {'科目ID':<10} {'科目名称':<15} {'渠道':<15} {'题目数':<10}")
        print("-" * 60)
        
        for idx, group in enumerate(groups[:10], 1):
            print(f"{idx:<6} {group['type_name']:<12} {str(group['subject_id']):<10} "
                  f"{group['subject_name'] or 'N/A':<15} {group['channel_code']:<15} {group['count']:<10}")
        
        if len(groups) > 10:
            print(f"... 还有 {len(groups) - 10} 个分组未显示")
        
        # 按题型统计
        print("\n4. 按题型统计分组数量：")
        type_stats = {}
        for group in groups:
            type_name = group['type_name']
            if type_name not in type_stats:
                type_stats[type_name] = {'group_count': 0, 'question_count': 0}
            type_stats[type_name]['group_count'] += 1
            type_stats[type_name]['question_count'] += group['count']
        
        for type_name, stats in type_stats.items():
            print(f"  - {type_name}: {stats['group_count']} 个分组, 共 {stats['question_count']} 题")
        
        return groups


def test_get_questions_by_group():
    """测试根据分组条件查询题目"""
    with app.app_context():
        # 先获取一个分组
        groups = QuestionService.get_question_groups()
        if not groups:
            print("没有找到任何分组")
            return
        
        # 使用第一个分组进行测试
        test_group = groups[0]
        print("\n" + "=" * 60)
        print("测试：根据分组条件查询题目")
        print("=" * 60)
        print(f"分组信息：")
        print(f"  - 题型：{test_group['type_name']} ({test_group['type']})")
        print(f"  - 科目ID：{test_group['subject_id']}")
        print(f"  - 渠道：{test_group['channel_code']}")
        print(f"  - 预期题目数：{test_group['count']}")
        
        # 查询该分组的题目
        questions = QuestionService.get_questions_by_group(
            question_type=test_group['type'],
            subject_id=test_group['subject_id'],
            channel_code=test_group['channel_code']
        )
        
        print(f"\n实际查询到的题目数：{len(questions)}")
        print(f"验证：{'✓ 通过' if len(questions) == test_group['count'] else '✗ 不匹配'}")


if __name__ == '__main__':
    try:
        # 测试分组查询
        groups = test_get_question_groups()
        
        # 测试根据分组查询题目
        if groups:
            test_get_questions_by_group()
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误：{e}")
        import traceback
        traceback.print_exc()

