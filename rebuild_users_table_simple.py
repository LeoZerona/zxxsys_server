"""简化版：重建 users 表（直接使用 SQLAlchemy）"""
from app import app, db
from models import User
from sqlalchemy import inspect

def rebuild_users_table_simple():
    """使用 SQLAlchemy 删除并重建 users 表"""
    with app.app_context():
        try:
            print("=" * 60)
            print("重建 users 表（SQLAlchemy 方式）")
            print("=" * 60)
            print()
            
            # 检查表是否存在
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'users' in tables:
                print("⚠️  检测到 users 表存在，正在删除...")
                # 删除表
                User.__table__.drop(db.engine, checkfirst=True)
                print("✅ users 表已删除")
            else:
                print("ℹ️  users 表不存在，直接创建新表")
            
            print()
            print("正在创建新的 users 表...")
            
            # 创建表（这会根据 models.py 中的定义创建，包含 role 字段）
            User.__table__.create(db.engine, checkfirst=True)
            
            print("✅ users 表创建成功")
            print()
            
            # 验证
            columns = inspector.get_columns('users')
            print("表结构验证:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
            
            print()
            print("=" * 60)
            print("✅ 重建完成！")
            print("=" * 60)
            print()
            print("注意：")
            print("- role 字段默认值为 'user'")
            print("- email 和 role 字段已建立索引")
            
            return True
        
        except Exception as e:
            print(f"\n❌ 重建失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("\n⚠️  警告：此操作将删除并重建 users 表！")
    print("   确保 users 表是空表或数据已备份。")
    print()
    
    confirm = input("确认继续？(yes/no): ").strip().lower()
    
    if confirm == 'yes':
        rebuild_users_table_simple()
    else:
        print("操作已取消")

