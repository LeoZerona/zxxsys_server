"""
检查题目去重相关表是否存在
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db


def check_tables():
    """检查表是否存在"""
    with app.app_context():
        print("=" * 60)
        print("检查题目去重相关数据库表")
        print("=" * 60)
        
        try:
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            expected_tables = [
                'dedup_tasks',
                'question_duplicate_pairs',
                'question_duplicate_groups',
                'question_duplicate_group_items',
                'question_dedup_features'
            ]
            
            print("\n检查结果：")
            missing_tables = []
            for table_name in expected_tables:
                if table_name in tables:
                    print(f"  ✅ {table_name}")
                else:
                    print(f"  ❌ {table_name} (不存在)")
                    missing_tables.append(table_name)
            
            if missing_tables:
                print(f"\n缺失的表：{len(missing_tables)} 个")
                print(f"需要创建：{', '.join(missing_tables)}")
                return False
            else:
                print("\n✅ 所有表都已创建！")
                return True
                
        except Exception as e:
            print(f"\n❌ 检查失败：{e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    check_tables()

