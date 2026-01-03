"""检查去重数据库中的数据"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db
from src.models.question_dedup import (
    DedupTask, QuestionDedupFeature, 
    QuestionDuplicatePair, QuestionDuplicateGroup,
    QuestionDuplicateGroupItem
)

with app.app_context():
    print("=" * 60)
    print("检查去重数据库中的数据")
    print("=" * 60)
    
    # 检查各个表的数据量
    tasks_count = DedupTask.query.count()
    features_count = QuestionDedupFeature.query.count()
    pairs_count = QuestionDuplicatePair.query.count()
    groups_count = QuestionDuplicateGroup.query.count()
    items_count = QuestionDuplicateGroupItem.query.count()
    
    print(f"\n数据统计:")
    print(f"  DedupTask (任务表): {tasks_count} 条")
    print(f"  QuestionDedupFeature (特征表): {features_count} 条")
    print(f"  QuestionDuplicatePair (重复对表): {pairs_count} 条")
    print(f"  QuestionDuplicateGroup (重复组表): {groups_count} 条")
    print(f"  QuestionDuplicateGroupItem (组明细表): {items_count} 条")
    
    if tasks_count > 0:
        print(f"\n任务列表:")
        tasks = DedupTask.query.order_by(DedupTask.created_at.desc()).all()
        for task in tasks[:5]:  # 只显示前5个
            print(f"  - 任务ID: {task.id}, 名称: {task.task_name}, 状态: {task.status}")
            print(f"    总分组: {task.total_groups}, 已处理: {task.processed_groups}")
            print(f"    创建时间: {task.created_at}")
    
    if features_count > 0:
        print(f"\n特征数据示例（前3条）:")
        features = QuestionDedupFeature.query.limit(3).all()
        for feat in features:
            print(f"  - 题目ID: {feat.question_id}, 任务ID: {feat.task_id}")
            print(f"    内容哈希: {feat.content_hash}")
            ngrams_count = len(feat.get_ngrams()) if feat.ngram_json else 0
            minhash_count = len(feat.get_minhash()) if feat.minhash_json else 0
            print(f"    N-gram数量: {ngrams_count}, MinHash长度: {minhash_count}")
    
    if pairs_count > 0:
        print(f"\n重复对示例（前3条）:")
        pairs = QuestionDuplicatePair.query.limit(3).all()
        for pair in pairs:
            print(f"  - 题目{pair.question_id_1} <-> 题目{pair.question_id_2}")
            print(f"    相似度: {pair.similarity}, 类型: {pair.duplicate_type}")
    
    if groups_count > 0:
        print(f"\n重复组示例（前3条）:")
        groups = QuestionDuplicateGroup.query.limit(3).all()
        for group in groups:
            items_count = group.items.count()
            print(f"  - 组ID: {group.id}, 题目数: {group.question_count}, 明细数: {items_count}")
            print(f"    内容哈希: {group.content_hash}")
    
    print("\n" + "=" * 60)
    if tasks_count == 0 and features_count == 0 and pairs_count == 0:
        print("结论: 数据库中没有去重相关的数据")
        print("说明: 测试脚本只处理数据，没有保存到数据库")
    else:
        print("结论: 数据库中有去重相关的数据")
    print("=" * 60)

