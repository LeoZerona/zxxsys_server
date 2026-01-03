"""查看找到的重复题目详情"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db
from src.models.question_dedup import DedupTask, QuestionDuplicateGroup, QuestionDuplicateGroupItem
from src.models.question import Question

with app.app_context():
    task_id = 3
    task = DedupTask.query.get(task_id)
    
    print("=" * 80)
    print(f"任务详情: {task.task_name}")
    print("=" * 80)
    print(f"任务ID: {task.id}")
    print(f"状态: {task.status}")
    print(f"已处理分组: {task.processed_groups}/{task.total_groups}")
    print(f"完全重复组数: {task.exact_duplicate_groups}")
    print(f"完全重复对数: {task.exact_duplicate_pairs}")
    
    # 查询该任务的完全重复组
    groups = QuestionDuplicateGroup.query.filter_by(task_id=task_id).all()
    print(f"\n找到的完全重复组数: {len(groups)}")
    
    for g in groups:
        items = g.items.all()
        print(f"\n" + "-" * 80)
        print(f"组ID: {g.id}")
        print(f"题目数: {g.question_count}")
        print(f"内容哈希: {g.content_hash}")
        print(f"题型: {g.group_type}, 科目ID: {g.group_subject_id}, 渠道: {g.group_channel_code}")
        print(f"题目ID列表: {[item.question_id for item in items]}")
        
        print(f"\n题目内容:")
        for item in items:
            q = Question.query.filter_by(question_id=item.question_id).first()
            if q:
                content = (q.content or "")[:200]
                print(f"  题目{item.question_id}: {content}{'...' if len(q.content or '') > 200 else ''}")
    
    print("\n" + "=" * 80)

