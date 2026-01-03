"""
测试单个分组的完整去重流程
挑选一种类型进行测试，并记录测试进度和类型安排
"""
import sys
import os
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db
from src.services.question_service import QuestionService
from src.services.question_dedup_service import QuestionDedupService


def select_test_group(groups, min_count=10, max_count=1000, prefer_small=True):
    """
    选择一个合适的分组进行测试
    
    Args:
        groups: 所有分组列表
        min_count: 最小题目数（避免题目太少）
        max_count: 最大题目数（避免题目太多，测试时间过长）
        prefer_small: 是否优先选择小规模分组
        
    Returns:
        选中的分组，如果没有合适的则返回None
    """
    # 筛选出题目数在合理范围内的分组
    suitable_groups = [
        g for g in groups 
        if min_count <= g['count'] <= max_count
    ]
    
    if not suitable_groups:
        # 如果没有合适的，选择题目数最接近max_count的
        suitable_groups = sorted(groups, key=lambda x: abs(x['count'] - max_count))[:5]
    
    if not suitable_groups:
        return None
    
    # 如果优先选择小规模，选择题目数最小的
    if prefer_small:
        selected = min(suitable_groups, key=lambda x: x['count'])
    else:
        # 否则选择题目数适中的
        target_count = (min_count + max_count) // 2
        selected = min(suitable_groups, key=lambda x: abs(x['count'] - target_count))
    
    return selected


def record_test_info(test_group, test_log_file='test_dedup_log.json'):
    """
    记录测试信息到文件
    
    Args:
        test_group: 测试分组信息
        test_log_file: 日志文件路径
    """
    test_info = {
        'test_date': datetime.now().isoformat(),
        'test_group': test_group,
        'test_status': 'started',
        'test_results': {}
    }
    
    # 读取现有日志（如果存在）
    if os.path.exists(test_log_file):
        try:
            with open(test_log_file, 'r', encoding='utf-8') as f:
                existing_logs = json.load(f)
        except:
            existing_logs = {'tests': []}
    else:
        existing_logs = {'tests': []}
    
    # 添加新测试
    if 'tests' not in existing_logs:
        existing_logs['tests'] = []
    existing_logs['tests'].append(test_info)
    
    # 保存日志
    with open(test_log_file, 'w', encoding='utf-8') as f:
        json.dump(existing_logs, f, ensure_ascii=False, indent=2)
    
    return test_info


def update_test_result(test_log_file='test_dedup_log.json', test_index=-1, results=None, status='completed'):
    """
    更新测试结果
    
    Args:
        test_log_file: 日志文件路径
        test_index: 测试索引（-1表示最后一个）
        results: 测试结果
        status: 测试状态
    """
    if not os.path.exists(test_log_file):
        return
    
    try:
        with open(test_log_file, 'r', encoding='utf-8') as f:
            logs = json.load(f)
        
        if 'tests' in logs and logs['tests']:
            test_info = logs['tests'][test_index]
            test_info['test_status'] = status
            test_info['test_results'] = results or {}
            test_info['completed_at'] = datetime.now().isoformat()
            
            with open(test_log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"更新测试日志失败: {e}")


def test_single_group_dedup():
    """测试单个分组的完整去重流程"""
    print("=" * 80)
    print("测试：单个分组完整去重流程")
    print("=" * 80)
    
    with app.app_context():
        # 1. 获取所有分组
        print("\n【步骤1】获取所有分组...")
        groups = QuestionService.get_question_groups()
        print(f"  共找到 {len(groups)} 个分组")
        
        # 显示分组统计信息
        total_questions = sum(g['count'] for g in groups)
        print(f"  总题目数: {total_questions}")
        
        # 按题型统计
        type_stats = {}
        for group in groups:
            type_name = group['type_name']
            if type_name not in type_stats:
                type_stats[type_name] = {'count': 0, 'groups': 0}
            type_stats[type_name]['count'] += group['count']
            type_stats[type_name]['groups'] += 1
        
        print(f"\n  按题型统计:")
        for type_name, stats in sorted(type_stats.items()):
            print(f"    - {type_name}: {stats['groups']} 个分组, {stats['count']} 题")
        
        # 2. 选择一个合适的分组进行测试
        print("\n【步骤2】选择测试分组...")
        test_group = select_test_group(groups, min_count=10, max_count=500)
        
        if not test_group:
            print("  错误：没有找到合适的分组进行测试")
            return
        
        print(f"  选中的测试分组:")
        print(f"    - 题型: {test_group['type_name']} ({test_group['type']})")
        print(f"    - 科目: {test_group['subject_name']} (ID: {test_group['subject_id']})")
        print(f"    - 渠道: {test_group['channel_code']}")
        print(f"    - 题目数: {test_group['count']}")
        
        # 记录测试信息
        test_log_file = 'test_dedup_log.json'
        test_info = record_test_info(test_group, test_log_file)
        
        # 3. 创建测试任务（用于保存数据到数据库）
        print("\n【步骤3】创建测试任务...")
        from src.models.question_dedup import DedupTask
        from src.models import db
        
        # 创建测试任务
        task_name = f"测试-{test_group['type_name']}-{test_group.get('subject_name', '未知科目')}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        task = DedupTask(
            task_name=task_name,
            status='running',
            total_groups=1,  # 只处理1个分组
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
        
        # 4. 处理该分组
        print("\n【步骤4】处理分组（完整流程）...")
        print("  " + "-" * 76)
        
        try:
            start_time = datetime.now()
            results = QuestionDedupService.process_single_group(test_group)
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            print(f"\n  处理完成！耗时: {processing_time:.2f} 秒")
            
            # 4.5 保存数据到数据库
            print("\n【步骤4.5】保存数据到数据库...")
            QuestionDedupService._save_group_results_to_db(task_id, results)
            print(f"  数据已保存到数据库（任务ID: {task_id}）")
            
            # 5. 显示测试结果
            print("\n【步骤5】测试结果统计...")
            print("  " + "-" * 76)
            
            print(f"\n  分组信息:")
            print(f"    - 题型: {results['group']['type_name']}")
            print(f"    - 科目: {results['group']['subject_name']}")
            print(f"    - 渠道: {results['group']['channel_code']}")
            print(f"    - 总题目数: {results['total_questions']}")
            
            # 打印所有题目的详细数据
            print(f"\n【所有题目数据】")
            print("  " + "=" * 76)
            from src.models.question import Question
            questions = QuestionService.get_questions_by_group(
                question_type=test_group['type'],
                subject_id=test_group['subject_id'],
                channel_code=test_group['channel_code']
            )
            cleaned_questions = results.get('cleaned_questions', [])
            
            for idx, question in enumerate(questions, 1):
                print(f"\n  题目 {idx} (ID: {question.question_id}):")
                print(f"    原始内容:")
                content = question.content or ""
                # 分行打印，每行最多80字符
                for line in content.split('\n'):
                    if line.strip():
                        print(f"      {line[:200]}{'...' if len(line) > 200 else ''}")
                
                # 查找对应的清洗后内容
                cleaned_data = next((q for q in cleaned_questions if q['question_id'] == question.question_id), None)
                if cleaned_data:
                    print(f"    清洗后内容:")
                    cleaned_content = cleaned_data.get('cleaned_content', '')
                    for line in cleaned_content.split('\n'):
                        if line.strip():
                            print(f"      {line[:200]}{'...' if len(line) > 200 else ''}")
                    print(f"    内容哈希: {cleaned_data.get('content_hash', 'N/A')}")
                    ngrams = cleaned_data.get('ngrams', [])
                    if ngrams:
                        print(f"    N-gram数量: {len(ngrams)}")
                        print(f"    N-gram示例（前10个）: {ngrams[:10]}")
                    minhash = cleaned_data.get('minhash', [])
                    if minhash:
                        print(f"    MinHash指纹长度: {len(minhash)}")
                        print(f"    MinHash示例（前10个）: {minhash[:10]}")
            
            print(f"\n  完全重复检测:")
            exact_duplicates = results.get('exact_duplicates', [])
            print(f"    - 完全重复组数: {len(exact_duplicates)}")
            if exact_duplicates:
                total_exact_dup_questions = sum(dup['count'] for dup in exact_duplicates)
                total_exact_dup_pairs = sum(dup['count'] * (dup['count'] - 1) // 2 for dup in exact_duplicates)
                print(f"    - 完全重复题目数: {total_exact_dup_questions}")
                print(f"    - 完全重复对数: {total_exact_dup_pairs}")
                
                # 显示前5个完全重复组
                print(f"\n    前5个完全重复组:")
                for i, dup in enumerate(exact_duplicates[:5], 1):
                    print(f"      组{i}: {dup['count']} 题, ID: {dup['question_ids'][:5]}{'...' if len(dup['question_ids']) > 5 else ''}")
            
            print(f"\n  相似重复检测:")
            similar_duplicates = results.get('similar_duplicates', [])
            print(f"    - 相似重复对数: {len(similar_duplicates)}")
            if similar_duplicates:
                # 统计相似度分布
                similarity_ranges = {
                    '0.8-0.85': 0,
                    '0.85-0.9': 0,
                    '0.9-0.95': 0,
                    '0.95-1.0': 0
                }
                for dup in similar_duplicates:
                    sim = dup['similarity']
                    if 0.8 <= sim < 0.85:
                        similarity_ranges['0.8-0.85'] += 1
                    elif 0.85 <= sim < 0.9:
                        similarity_ranges['0.85-0.9'] += 1
                    elif 0.9 <= sim < 0.95:
                        similarity_ranges['0.9-0.95'] += 1
                    elif 0.95 <= sim <= 1.0:
                        similarity_ranges['0.95-1.0'] += 1
                
                print(f"\n    相似度分布:")
                for range_name, count in similarity_ranges.items():
                    if count > 0:
                        print(f"      - {range_name}: {count} 对")
                
                # 显示所有相似重复对的详细信息
                print(f"\n    相似重复对详情（显示所有对）:")
                from src.models.question import Question
                for i, dup in enumerate(similar_duplicates, 1):
                    print(f"\n      对{i}: 题目{dup['question_id_1']} <-> 题目{dup['question_id_2']}")
                    print(f"        相似度: {dup['similarity']:.4f} ({dup['similarity']*100:.2f}%)")
                    
                    # 查询并显示两个题目的内容
                    q1 = Question.query.filter_by(question_id=dup['question_id_1']).first()
                    q2 = Question.query.filter_by(question_id=dup['question_id_2']).first()
                    
                    if q1:
                        content1 = (q1.content or "")[:150]
                        print(f"        题目{dup['question_id_1']}内容:")
                        print(f"          {content1}{'...' if len(q1.content or '') > 150 else ''}")
                    
                    if q2:
                        content2 = (q2.content or "")[:150]
                        print(f"        题目{dup['question_id_2']}内容:")
                        print(f"          {content2}{'...' if len(q2.content or '') > 150 else ''}")
                    
                    # 显示清洗后的内容
                    cleaned_content = results.get('cleaned_questions', [])
                    cleaned1 = next((q for q in cleaned_content if q['question_id'] == dup['question_id_1']), None)
                    cleaned2 = next((q for q in cleaned_content if q['question_id'] == dup['question_id_2']), None)
                    
                    if cleaned1:
                        cleaned_preview1 = (cleaned1.get('cleaned_content', ''))[:150]
                        print(f"        题目{dup['question_id_1']}清洗后:")
                        print(f"          {cleaned_preview1}{'...' if len(cleaned1.get('cleaned_content', '')) > 150 else ''}")
                    
                    if cleaned2:
                        cleaned_preview2 = (cleaned2.get('cleaned_content', ''))[:150]
                        print(f"        题目{dup['question_id_2']}清洗后:")
                        print(f"          {cleaned_preview2}{'...' if len(cleaned2.get('cleaned_content', '')) > 150 else ''}")
            
            print(f"\n  特征数据:")
            cleaned_questions = results.get('cleaned_questions', [])
            print(f"    - 保存特征数据的题目数: {len(cleaned_questions)}")
            
            # 6. 保存测试结果
            test_results = {
                'processing_time_seconds': processing_time,
                'total_questions': results['total_questions'],
                'exact_duplicate_groups': len(exact_duplicates),
                'exact_duplicate_pairs': sum(dup['count'] * (dup['count'] - 1) // 2 for dup in exact_duplicates),
                'similar_duplicate_pairs': len(similar_duplicates),
                'features_saved': len(cleaned_questions),
                'processed_at': results.get('processed_at')
            }
            
            update_test_result(test_log_file, test_index=-1, results=test_results, status='completed')
            
            # 更新任务状态为完成
            task = DedupTask.query.get(task_id)
            if task:
                task.status = 'completed'
                task.completed_at = datetime.now()
                db.session.commit()
            
            print("\n【步骤6】测试结果已保存")
            print(f"  - 日志文件: {test_log_file}")
            print(f"  - 数据库任务ID: {task_id}")
            print(f"  - 任务名称: {task_name}")
            
            print("\n" + "=" * 80)
            print("测试完成！")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n  错误：{e}")
            import traceback
            traceback.print_exc()
            update_test_result(test_log_file, test_index=-1, results={'error': str(e)}, status='error')
            raise


if __name__ == '__main__':
    try:
        test_single_group_dedup()
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()

