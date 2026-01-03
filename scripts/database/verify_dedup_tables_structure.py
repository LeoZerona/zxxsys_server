"""
验证题目去重表的表结构
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db


def verify_table_structure():
    """验证表结构"""
    with app.app_context():
        print("=" * 60)
        print("验证题目去重表结构")
        print("=" * 60)
        
        inspector = db.inspect(db.engine)
        
        tables_info = {
            'dedup_tasks': [
                'id', 'task_name', 'status', 'total_groups', 'processed_groups',
                'total_questions', 'exact_duplicate_groups', 'exact_duplicate_pairs',
                'similar_duplicate_pairs', 'started_at', 'completed_at',
                'error_message', 'config_json', 'created_at', 'updated_at'
            ],
            'question_duplicate_pairs': [
                'id', 'task_id', 'question_id_1', 'question_id_2', 'similarity',
                'duplicate_type', 'group_type', 'group_subject_id',
                'group_channel_code', 'detected_at'
            ],
            'question_duplicate_groups': [
                'id', 'task_id', 'content_hash', 'question_count',
                'group_type', 'group_subject_id', 'group_channel_code', 'detected_at'
            ],
            'question_duplicate_group_items': [
                'id', 'group_id', 'task_id', 'question_id'
            ],
            'question_dedup_features': [
                'id', 'task_id', 'question_id', 'cleaned_content', 'content_hash',
                'ngram_json', 'minhash_json', 'group_type', 'group_subject_id',
                'group_channel_code', 'created_at'
            ]
        }
        
        all_correct = True
        
        for table_name, expected_columns in tables_info.items():
            print(f"\n检查表: {table_name}")
            try:
                columns = [col['name'] for col in inspector.get_columns(table_name)]
                
                missing = [col for col in expected_columns if col not in columns]
                extra = [col for col in columns if col not in expected_columns]
                
                if missing:
                    print(f"  ❌ 缺失字段: {', '.join(missing)}")
                    all_correct = False
                if extra:
                    print(f"  ⚠️  额外字段: {', '.join(extra)}")
                if not missing and not extra:
                    print(f"  ✅ 表结构正确 ({len(columns)} 个字段)")
                else:
                    print(f"  实际字段: {', '.join(columns)}")
                    
            except Exception as e:
                print(f"  ❌ 检查失败: {e}")
                all_correct = False
        
        if all_correct:
            print("\n" + "=" * 60)
            print("✅ 所有表结构验证通过！")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ 部分表结构不正确，请检查")
            print("=" * 60)
        
        return all_correct


if __name__ == '__main__':
    verify_table_structure()

