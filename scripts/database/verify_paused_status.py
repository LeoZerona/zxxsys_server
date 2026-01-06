"""
验证脚本：检查 dedup_tasks 表的 status 字段是否支持 'paused' 状态
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db
from sqlalchemy import text, inspect


def verify_paused_status():
    """验证 status 字段是否支持 'paused' 状态"""
    with app.app_context():
        try:
            # 检测数据库类型
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            
            print("=" * 60)
            print("验证 dedup_tasks 表的 status 字段")
            print("=" * 60)
            print(f"数据库类型: {db_url.split('://')[0]}")
            print()
            
            # 检查表是否存在
            inspector = inspect(db.engine)
            if 'dedup_tasks' not in inspector.get_table_names():
                print("❌ 错误：dedup_tasks 表不存在")
                return False
            
            # 根据数据库类型检查
            if 'sqlite' in db_url.lower():
                # SQLite 使用 VARCHAR，检查字段类型
                columns = inspector.get_columns('dedup_tasks')
                status_col = next((col for col in columns if col['name'] == 'status'), None)
                if status_col:
                    col_type = str(status_col['type'])
                    print(f"✅ status 字段类型: {col_type}")
                    print("✅ SQLite 使用 VARCHAR，支持 'paused' 状态")
                    return True
                else:
                    print("❌ 未找到 status 字段")
                    return False
            
            elif 'mysql' in db_url.lower():
                # MySQL 使用 ENUM，检查 ENUM 值
                result = db.session.execute(text("""
                    SELECT COLUMN_TYPE 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                      AND TABLE_NAME = 'dedup_tasks' 
                      AND COLUMN_NAME = 'status';
                """))
                row = result.fetchone()
                if row:
                    enum_def = row[0]
                    print(f"当前 ENUM 定义: {enum_def}")
                    
                    if 'paused' in str(enum_def).lower():
                        print("✅ 'paused' 状态已包含在 ENUM 中")
                        return True
                    else:
                        print("❌ 'paused' 状态未包含在 ENUM 中")
                        print()
                        print("请运行修复脚本：")
                        print("  python scripts/database/fix_paused_status.py")
                        return False
                else:
                    print("❌ 未找到 status 字段")
                    return False
            
            elif 'postgresql' in db_url.lower() or 'postgres' in db_url.lower():
                # PostgreSQL 使用 VARCHAR，检查字段类型
                columns = inspector.get_columns('dedup_tasks')
                status_col = next((col for col in columns if col['name'] == 'status'), None)
                if status_col:
                    col_type = str(status_col['type'])
                    print(f"✅ status 字段类型: {col_type}")
                    print("✅ PostgreSQL 使用 VARCHAR，支持 'paused' 状态")
                    return True
                else:
                    print("❌ 未找到 status 字段")
                    return False
            
            else:
                print(f"❌ 不支持的数据库类型: {db_url.split('://')[0]}")
                return False
            
        except Exception as e:
            print(f"❌ 验证失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    success = verify_paused_status()
    print()
    if success:
        print("=" * 60)
        print("✅ 验证通过：status 字段支持 'paused' 状态")
        print("=" * 60)
    else:
        print("=" * 60)
        print("❌ 验证失败：status 字段不支持 'paused' 状态")
        print("=" * 60)
        print()
        print("请运行修复脚本：")
        print("  python scripts/database/fix_paused_status.py")
    sys.exit(0 if success else 1)

