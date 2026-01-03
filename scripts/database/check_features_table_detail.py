"""检查特征表详细结构"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db
from src.models.question_dedup import QuestionDedupFeature

with app.app_context():
    print("=" * 60)
    print("检查特征表结构")
    print("=" * 60)
    
    # 检查表是否存在
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    
    if 'question_dedup_features' not in tables:
        print("❌ 表不存在")
    else:
        print("✅ 表已存在：question_dedup_features")
        print("\n表结构：")
        print("-" * 60)
        
        cols = inspector.get_columns('question_dedup_features')
        required_fields = {
            'cleaned_content': 'TEXT',
            'content_hash': 'VARCHAR',
            'ngram_json': 'TEXT',
            'minhash_json': 'TEXT'
        }
        
        found_fields = {}
        for col in cols:
            col_name = col['name']
            col_type = str(col['type'])
            print(f"  {col_name:20} {col_type}")
            if col_name in required_fields:
                found_fields[col_name] = col_type
        
        print("\n必需字段检查：")
        print("-" * 60)
        all_found = True
        for field, expected_type in required_fields.items():
            if field in found_fields:
                print(f"  ✅ {field:20} ({found_fields[field]})")
            else:
                print(f"  ❌ {field:20} (缺失)")
                all_found = False
        
        if all_found:
            print("\n✅ 所有必需字段都已存在，表结构完整！")
        else:
            print("\n❌ 部分必需字段缺失，需要添加")
        
        # 检查索引
        print("\n索引检查：")
        print("-" * 60)
        indexes = inspector.get_indexes('question_dedup_features')
        for idx in indexes:
            print(f"  ✅ {idx['name']:20} {', '.join(idx['column_names'])}")
        
        # 检查唯一约束
        print("\n唯一约束检查：")
        print("-" * 60)
        unique_constraints = inspector.get_unique_constraints('question_dedup_features')
        for uc in unique_constraints:
            print(f"  ✅ {uc['name']:20} {', '.join(uc['column_names'])}")

