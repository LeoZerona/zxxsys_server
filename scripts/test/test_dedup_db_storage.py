"""
测试题目去重服务的数据库存储功能
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db
from src.services.question_dedup_service import QuestionDedupService
from src.models.question_dedup import DedupTask, QuestionDuplicateGroup, QuestionDuplicatePair


def test_db_storage():
    """测试数据库存储功能"""
    with app.app_context():
        print("=" * 60)
        print("测试：数据库存储功能")
        print("=" * 60)
        
        # 1. 测试初始化会话（创建任务记录）
        print("\n1. 测试初始化会话...")
        progress = QuestionDedupService.init_dedup_session(task_name="测试任务")
        task_id = progress.get('task_id')
        print(f"   任务ID: {task_id}")
        print(f"   总分组数: {progress['total_groups']}")
        
        # 验证任务记录是否创建
        task = DedupTask.query.get(task_id)
        if task:
            print(f"   ✅ 任务记录创建成功: {task.task_name}, 状态: {task.status}")
        else:
            print(f"   ❌ 任务记录未找到")
            return
        
        # 2. 测试处理一个分组
        print("\n2. 测试处理分组并保存到数据库...")
        results = QuestionDedupService.process_next_group()
        
        if results:
            print(f"   处理分组: {results['group']['type_name']} - {results['group']['subject_name']}")
            print(f"   完全重复组数: {len(results['exact_duplicates'])}")
            
            # 标记完成（会保存到数据库）
            QuestionDedupService.mark_group_completed(results)
            
            # 验证数据是否保存到数据库
            groups_in_db = QuestionDuplicateGroup.query.filter_by(task_id=task_id).count()
            pairs_in_db = QuestionDuplicatePair.query.filter_by(task_id=task_id).count()
            
            print(f"\n   数据库验证:")
            print(f"   完全重复组数（数据库）: {groups_in_db}")
            print(f"   重复对数（数据库）: {pairs_in_db}")
            
            # 更新后的任务统计
            db.session.refresh(task)
            print(f"\n   任务统计更新:")
            print(f"   已处理分组: {task.processed_groups}/{task.total_groups}")
            print(f"   完全重复组数: {task.exact_duplicate_groups}")
            print(f"   完全重复对数: {task.exact_duplicate_pairs}")
            print(f"   总题目数: {task.total_questions}")
        else:
            print("   没有找到分组")
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)


if __name__ == '__main__':
    try:
        test_db_storage()
    except Exception as e:
        print(f"\n错误：{e}")
        import traceback
        traceback.print_exc()

