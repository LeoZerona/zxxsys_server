"""显示找到的重复题目结果"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db
from src.models.question_dedup import DedupTask, QuestionDuplicateGroup, QuestionDuplicateGroupItem, QuestionDuplicatePair
from src.models.question import Question

def show_duplicate_result(task_id=3):
    """显示重复题目结果"""
    with app.app_context():
        task = DedupTask.query.get(task_id)
        if not task:
            print(f"任务ID {task_id} 不存在")
            return
        
        print("=" * 80)
        print("处理统计")
        print("=" * 80)
        print(f"任务ID: {task.id}")
        print(f"任务名称: {task.task_name}")
        print(f"总分组数: {task.total_groups}")
        print(f"已处理分组数: {task.processed_groups}")
        
        # 检查是否有重复
        has_duplicates = task.exact_duplicate_groups > 0 or task.similar_duplicate_pairs > 0
        print(f"找到重复: {'是' if has_duplicates else '否'}")
        
        if has_duplicates:
            print("\n" + "=" * 80)
            print("找到的重复题目")
            print("=" * 80)
            
            # 查询完全重复组
            exact_groups = QuestionDuplicateGroup.query.filter_by(task_id=task_id).all()
            
            if exact_groups:
                print(f"\n完全重复组: {len(exact_groups)}组")
                print(f"完全重复对数: {task.exact_duplicate_pairs}")
                print()
                
                for idx, group in enumerate(exact_groups, 1):
                    items = group.items.all()
                    question_ids = [item.question_id for item in items]
                    
                    print(f"【完全重复组 {idx}】")
                    print(f"题型: {group.group_type}", end="")
                    
                    # 获取题型名称
                    type_names = {
                        '1': '单选题',
                        '2': '多选题',
                        '3': '判断题',
                        '4': '填空题',
                        '8': '计算分析题'
                    }
                    type_name = type_names.get(group.group_type, '未知题型')
                    print(f" ({type_name})")
                    
                    print(f"科目ID: {group.group_subject_id}", end="")
                    
                    # 查询科目名称（从题目表中获取）
                    if question_ids:
                        first_question = Question.query.filter_by(question_id=question_ids[0]).first()
                        if first_question and first_question.subject_name:
                            print(f" ({first_question.subject_name})")
                        else:
                            print()
                    else:
                        print()
                    
                    print(f"渠道: {group.group_channel_code}")
                    print(f"重复题目ID: {', '.join(map(str, question_ids))}")
                    print(f"题目数量: {group.question_count}")
                    print(f"内容哈希: {group.content_hash}")
                    
                    # 显示题目内容
                    print(f"\n题目内容:")
                    for qid in question_ids:
                        q = Question.query.filter_by(question_id=qid).first()
                        if q:
                            content = (q.content or "").strip()
                            # 去除HTML标签用于显示
                            import re
                            clean_content = re.sub(r'<[^>]+>', '', content)
                            clean_content = clean_content[:150]  # 限制长度
                            print(f"  题目{qid}: {clean_content}{'...' if len(q.content or '') > 150 else ''}")
                    
                    print()
            
            # 查询相似重复对
            similar_pairs = QuestionDuplicatePair.query.filter_by(
                task_id=task_id,
                duplicate_type='similar'
            ).all()
            
            if similar_pairs:
                print(f"\n相似重复对: {len(similar_pairs)}对")
                print()
                
                for idx, pair in enumerate(similar_pairs, 1):
                    print(f"【相似重复对 {idx}】")
                    print(f"题目{pair.question_id_1} <-> 题目{pair.question_id_2}")
                    print(f"相似度: {float(pair.similarity):.4f} ({float(pair.similarity)*100:.2f}%)")
                    print(f"题型: {pair.group_type}")
                    print(f"科目ID: {pair.group_subject_id}")
                    print(f"渠道: {pair.group_channel_code}")
                    
                    # 显示题目内容
                    q1 = Question.query.filter_by(question_id=pair.question_id_1).first()
                    q2 = Question.query.filter_by(question_id=pair.question_id_2).first()
                    
                    if q1:
                        import re
                        content1 = re.sub(r'<[^>]+>', '', q1.content or "")
                        content1 = content1[:100]
                        print(f"  题目{pair.question_id_1}: {content1}{'...' if len(q1.content or '') > 100 else ''}")
                    
                    if q2:
                        import re
                        content2 = re.sub(r'<[^>]+>', '', q2.content or "")
                        content2 = content2[:100]
                        print(f"  题目{pair.question_id_2}: {content2}{'...' if len(q2.content or '') > 100 else ''}")
                    
                    print()
        
        print("=" * 80)


if __name__ == '__main__':
    import sys
    task_id = 3
    if len(sys.argv) > 1:
        try:
            task_id = int(sys.argv[1])
        except ValueError:
            print(f"错误：无效的任务ID: {sys.argv[1]}")
            sys.exit(1)
    
    try:
        show_duplicate_result(task_id)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()