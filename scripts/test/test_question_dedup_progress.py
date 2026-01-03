"""
测试题目去重服务的进度管理功能
验证单分组处理和断点续传功能
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db
from src.services.question_dedup_service import QuestionDedupService


def test_progress_management():
    """测试进度管理功能"""
    with app.app_context():
        print("=" * 60)
        print("测试：进度管理功能")
        print("=" * 60)
        
        # 1. 重置进度（重新开始）
        print("\n1. 初始化去重会话...")
        progress = QuestionDedupService.init_dedup_session()
        print(f"   总分组数: {progress['total_groups']}")
        print(f"   当前分组索引: {progress['current_group_index']}")
        
        # 2. 获取处理摘要
        print("\n2. 获取处理摘要...")
        summary = QuestionDedupService.get_summary()
        print(f"   状态: {summary['status']}")
        print(f"   总分组数: {summary['total_groups']}")
        print(f"   已处理: {summary['processed_groups']}")
        print(f"   剩余: {summary['remaining_groups']}")
        print(f"   进度: {summary['progress_percentage']:.2f}%")
        
        # 3. 处理前3个分组
        print("\n3. 处理前3个分组...")
        for i in range(3):
            print(f"\n--- 处理第 {i+1} 个分组 ---")
            
            # 获取下一个分组
            group = QuestionDedupService.get_next_group()
            if not group:
                print("所有分组都已处理完成！")
                break
            
            print(f"分组信息:")
            print(f"  - 题型: {group['type_name']} ({group['type']})")
            print(f"  - 科目: {group['subject_name']} (ID: {group['subject_id']})")
            print(f"  - 渠道: {group['channel_code']}")
            print(f"  - 题目数: {group['count']}")
            
            # 处理分组（当前只是框架，返回空结果）
            results = QuestionDedupService.process_single_group(group)
            print(f"处理结果: 共 {results['total_questions']} 题")
            
            # 标记完成
            QuestionDedupService.mark_group_completed(results)
            
            # 显示进度
            summary = QuestionDedupService.get_summary()
            print(f"进度: {summary['processed_groups']}/{summary['total_groups']} ({summary['progress_percentage']:.2f}%)")
        
        # 4. 验证进度保存
        print("\n4. 验证进度保存...")
        progress = QuestionDedupService.get_progress()
        print(f"   当前分组索引: {progress['current_group_index']}")
        print(f"   已处理分组数: {progress['processed_groups']}")
        print(f"   状态: {progress['status']}")
        print(f"   最后更新: {progress['last_update']}")
        
        # 5. 模拟中断后继续处理
        print("\n5. 模拟中断后继续处理下一个分组...")
        group = QuestionDedupService.get_next_group()
        if group:
            print(f"下一个分组: {group['type_name']} - {group['subject_name']}")
            print(f"题目数: {group['count']}")
        else:
            print("所有分组都已处理完成！")
        
        # 6. 最终摘要
        print("\n6. 最终处理摘要...")
        summary = QuestionDedupService.get_summary()
        print(f"   状态: {summary['status']}")
        print(f"   总分组数: {summary['total_groups']}")
        print(f"   已处理: {summary['processed_groups']}")
        print(f"   剩余: {summary['remaining_groups']}")
        print(f"   进度: {summary['progress_percentage']:.2f}%")
        
        print("\n" + "=" * 60)
        print("测试完成！进度文件已保存，支持中断后继续处理。")
        print("=" * 60)


def test_process_next_group():
    """测试便捷方法：处理下一个分组"""
    with app.app_context():
        print("\n" + "=" * 60)
        print("测试：便捷方法 process_next_group()")
        print("=" * 60)
        
        # 处理一个分组
        results = QuestionDedupService.process_next_group()
        if results:
            print(f"\n处理完成:")
            print(f"  - 分组: {results['group']['type_name']} - {results['group']['subject_name']}")
            print(f"  - 题目数: {results['total_questions']}")
            print(f"  - 处理时间: {results['processed_at']}")
        else:
            print("\n所有分组都已处理完成！")


if __name__ == '__main__':
    try:
        # 测试进度管理
        test_progress_management()
        
        # 测试便捷方法
        # test_process_next_group()
        
    except Exception as e:
        print(f"\n错误：{e}")
        import traceback
        traceback.print_exc()

