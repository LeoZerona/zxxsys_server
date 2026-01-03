"""
循环处理分组，直到找到有重复性的题目时暂停
记录已处理的分组，并将数据写入数据库
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db
from src.services.question_service import QuestionService
from src.services.question_dedup_service import QuestionDedupService
from src.models.question_dedup import (
    DedupTask, QuestionDedupFeature,
    QuestionDuplicateGroup, QuestionDuplicatePair
)


def get_processed_groups(task_id):
    """获取已处理的分组列表"""
    # 从特征表中查询已处理的分组
    processed = db.session.query(
        QuestionDedupFeature.group_type,
        QuestionDedupFeature.group_subject_id,
        QuestionDedupFeature.group_channel_code
    ).filter(
        QuestionDedupFeature.task_id == task_id
    ).distinct().all()
    
    # 转换为集合，便于比较
    processed_set = set()
    for p in processed:
        processed_set.add((p[0], p[1], p[2]))
    
    return processed_set


def test_find_duplicates():
    """循环处理分组，直到找到有重复的分组"""
    print("=" * 80)
    print("循环处理分组，查找有重复性的题目")
    print("=" * 80)
    
    with app.app_context():
        # 1. 创建任务
        print("\n【步骤1】创建去重任务...")
        task_name = f"查找重复题目-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task = DedupTask(
            task_name=task_name,
            status='running',
            total_groups=0,  # 稍后更新
            processed_groups=0,
            total_questions=0,
            exact_duplicate_groups=0,
            exact_duplicate_pairs=0,
            similar_duplicate_pairs=0
        )
        db.session.add(task)
        db.session.commit()
        task_id = task.id
        print(f"  任务已创建: ID={task_id}, 名称={task_name}")
        
        # 2. 获取所有分组
        print("\n【步骤2】获取所有分组...")
        groups = QuestionService.get_question_groups()
        print(f"  共找到 {len(groups)} 个分组")
        
        # 3. 获取已处理的分组
        print("\n【步骤3】检查已处理的分组...")
        processed_groups = get_processed_groups(task_id)
        print(f"  已处理的分组数: {len(processed_groups)}")
        
        # 4. 筛选出未处理的分组（优先选择小规模分组）
        print("\n【步骤4】筛选未处理的分组...")
        unprocessed_groups = []
        for group in groups:
            group_key = (group['type'], group['subject_id'], group['channel_code'])
            if group_key not in processed_groups:
                unprocessed_groups.append(group)
        
        # 按题目数排序，优先处理小规模分组
        unprocessed_groups.sort(key=lambda x: x['count'])
        
        print(f"  未处理的分组数: {len(unprocessed_groups)}")
        if unprocessed_groups:
            print(f"  最小分组: {unprocessed_groups[0]['count']} 题")
            print(f"  最大分组: {unprocessed_groups[-1]['count']} 题")
        
        # 5. 更新任务总分组数
        task.total_groups = len(groups)
        db.session.commit()
        
        # 6. 循环处理分组，直到找到有重复的分组
        print("\n【步骤5】开始处理分组...")
        print("  " + "-" * 76)
        
        found_duplicates = False
        processed_count = 0
        
        for idx, group in enumerate(unprocessed_groups, 1):
            group_key = (group['type'], group['subject_id'], group['channel_code'])
            
            # 检查是否已处理（双重检查）
            if group_key in processed_groups:
                print(f"\n分组 {idx}/{len(unprocessed_groups)}: 已跳过（已处理）")
                continue
            
            print(f"\n【处理分组 {idx}/{len(unprocessed_groups)}】")
            print(f"  题型: {group['type_name']} ({group['type']})")
            print(f"  科目: {group.get('subject_name', 'None')} (ID: {group['subject_id']})")
            print(f"  渠道: {group['channel_code']}")
            print(f"  题目数: {group['count']}")
            
            try:
                # 处理该分组
                start_time = datetime.now()
                results = QuestionDedupService.process_single_group(group)
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                
                # 保存数据到数据库
                QuestionDedupService._save_group_results_to_db(task_id, results)
                
                # 更新已处理分组集合
                processed_groups.add(group_key)
                processed_count += 1
                
                # 更新任务进度
                task.processed_groups = processed_count
                db.session.commit()
                
                # 检查是否有重复
                exact_duplicates = results.get('exact_duplicates', [])
                similar_duplicates = results.get('similar_duplicates', [])
                has_duplicates = len(exact_duplicates) > 0 or len(similar_duplicates) > 0
                
                print(f"\n  处理完成！耗时: {processing_time:.2f} 秒")
                print(f"  完全重复组数: {len(exact_duplicates)}")
                print(f"  相似重复对数: {len(similar_duplicates)}")
                print(f"  特征数据保存: {len(results.get('cleaned_questions', []))} 条")
                
                if has_duplicates:
                    print(f"\n  ✅ 找到重复题目！")
                    found_duplicates = True
                    
                    # 显示重复详情
                    if exact_duplicates:
                        print(f"\n  完全重复组详情:")
                        total_exact_pairs = 0
                        for i, dup in enumerate(exact_duplicates, 1):
                            pairs = dup['count'] * (dup['count'] - 1) // 2
                            total_exact_pairs += pairs
                            print(f"    组{i}: {dup['count']} 题, ID: {dup['question_ids']}, 对数: {pairs}")
                        print(f"    总对数: {total_exact_pairs}")
                    
                    if similar_duplicates:
                        print(f"\n  相似重复对详情:")
                        for i, dup in enumerate(similar_duplicates, 1):
                            print(f"    对{i}: 题目{dup['question_id_1']} <-> 题目{dup['question_id_2']}, 相似度: {dup['similarity']:.4f}")
                    
                    # 暂停处理
                    print(f"\n  ⏸ 暂停处理（已找到重复题目）")
                    break
                else:
                    print(f"  ✓ 无重复，继续处理下一个分组...")
                    
            except Exception as e:
                print(f"\n  ❌ 处理失败: {e}")
                import traceback
                traceback.print_exc()
                # 记录错误但不中断，继续处理下一个分组
                continue
        
        # 7. 更新任务状态
        print("\n【步骤6】更新任务状态...")
        if found_duplicates:
            task.status = 'completed'  # 找到重复就完成
            print(f"  ✅ 任务完成：已找到重复题目")
        else:
            task.status = 'running'  # 未找到重复，任务继续运行
            print(f"  ⚠ 任务继续运行：未找到重复题目（已处理 {processed_count} 个分组）")
        
        task.completed_at = datetime.now() if found_duplicates else None
        db.session.commit()
        
        # 8. 最终统计
        print("\n" + "=" * 80)
        print("处理完成统计")
        print("=" * 80)
        print(f"  任务ID: {task_id}")
        print(f"  任务名称: {task_name}")
        print(f"  总分组数: {len(groups)}")
        print(f"  已处理分组数: {processed_count}")
        print(f"  是否找到重复: {'是' if found_duplicates else '否'}")
        
        if found_duplicates:
            print(f"\n  ✅ 已找到重复题目，处理已暂停")
            
            # 显示找到的重复题目详情
            print("\n" + "=" * 80)
            print("找到的重复题目详情")
            print("=" * 80)
            
            # 查询完全重复组
            exact_groups = QuestionDuplicateGroup.query.filter_by(task_id=task_id).all()
            if exact_groups:
                type_names = {
                    '1': '单选题',
                    '2': '多选题',
                    '3': '判断题',
                    '4': '填空题',
                    '8': '计算分析题'
                }
                
                for idx, group in enumerate(exact_groups, 1):
                    items = group.items.all()
                    question_ids = [item.question_id for item in items]
                    type_name = type_names.get(group.group_type, '未知题型')
                    
                    print(f"\n【完全重复组 {idx}】")
                    print(f"题型: {group.group_type} ({type_name})")
                    print(f"科目ID: {group.group_subject_id}", end="")
                    
                    # 查询科目名称
                    if question_ids:
                        from src.models.question import Question
                        first_question = Question.query.filter_by(question_id=question_ids[0]).first()
                        if first_question and first_question.subject_name:
                            print(f" ({first_question.subject_name})")
                        else:
                            print()
                    else:
                        print()
                    
                    print(f"渠道: {group.group_channel_code}")
                    print(f"完全重复组: {len(exact_groups)}组")
                    print(f"重复题目ID: {', '.join(map(str, question_ids))}")
                    print(f"完全重复对数: {group.question_count * (group.question_count - 1) // 2}")
            
            # 查询相似重复对
            similar_pairs = QuestionDuplicatePair.query.filter_by(
                task_id=task_id,
                duplicate_type='similar'
            ).all()
            if similar_pairs:
                print(f"\n相似重复对: {len(similar_pairs)}对")
                for idx, pair in enumerate(similar_pairs, 1):
                    print(f"  对{idx}: 题目{pair.question_id_1} <-> 题目{pair.question_id_2}, 相似度: {float(pair.similarity):.4f}")
        else:
            print(f"\n  ⚠ 未找到重复题目，可以继续处理更多分组")
        
        print("\n" + "=" * 80)


if __name__ == '__main__':
    try:
        test_find_duplicates()
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
