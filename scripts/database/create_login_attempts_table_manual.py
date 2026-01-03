"""
手动创建 login_attempts 表的脚本
如果应用启动时没有自动创建表，可以运行此脚本手动创建
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from src.app import app
from src.models import db, LoginAttempt

def create_table():
    """创建 login_attempts 表"""
    with app.app_context():
        try:
            print("=" * 80)
            print("📊 创建 login_attempts 表")
            print("=" * 80)
            
            # 检查表是否已存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if 'login_attempts' in existing_tables:
                print("✅ login_attempts 表已存在")
                print("\n表结构:")
                columns = inspector.get_columns('login_attempts')
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
            else:
                print("📝 创建 login_attempts 表...")
                # 创建表
                LoginAttempt.__table__.create(db.engine, checkfirst=True)
                print("✅ login_attempts 表创建成功")
            
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ 创建表失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    create_table()

