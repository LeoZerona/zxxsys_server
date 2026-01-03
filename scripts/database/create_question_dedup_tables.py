"""
创建题目去重相关数据库表
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db
from src.models.question_dedup import (
    DedupTask, QuestionDuplicatePair, QuestionDuplicateGroup,
    QuestionDuplicateGroupItem, QuestionDedupFeature
)


def create_tables():
    """创建所有去重相关表"""
    with app.app_context():
        print("=" * 60)
        print("创建题目去重相关数据库表")
        print("=" * 60)
        
        try:
            # 创建所有表
            db.create_all()
            
            print("\n✅ 表创建成功！")
            print("\n创建的表：")
            print("  1. dedup_tasks - 去重任务表")
            print("  2. question_duplicate_pairs - 重复题目对表")
            print("  3. question_duplicate_groups - 完全重复题目组表")
            print("  4. question_duplicate_group_items - 完全重复组明细表")
            print("  5. question_dedup_features - 题目去重特征表")
            
            # 验证表是否存在
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            expected_tables = [
                'dedup_tasks',
                'question_duplicate_pairs',
                'question_duplicate_groups',
                'question_duplicate_group_items',
                'question_dedup_features'
            ]
            
            print("\n验证表是否存在：")
            for table_name in expected_tables:
                if table_name in tables:
                    print(f"  ✅ {table_name}")
                else:
                    print(f"  ❌ {table_name} (未找到)")
            
        except Exception as e:
            print(f"\n❌ 创建表失败：{e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True


if __name__ == '__main__':
    create_tables()

