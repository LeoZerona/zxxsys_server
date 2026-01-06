"""
直接修复脚本：为 dedup_tasks 表的 status 字段添加 'paused' 状态支持
这个脚本会直接执行 SQL 来修复数据库表结构
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db
from sqlalchemy import text, inspect


def fix_paused_status():
    """直接修复 status 字段，添加 'paused' 状态"""
    with app.app_context():
        try:
            # 检测数据库类型
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            
            print("=" * 60)
            print("修复 dedup_tasks 表的 status 字段")
            print("=" * 60)
            print(f"数据库连接: {db_url.split('@')[-1] if '@' in db_url else db_url}")
            print()
            
            # 检查表是否存在
            inspector = inspect(db.engine)
            if 'dedup_tasks' not in inspector.get_table_names():
                print("❌ 错误：dedup_tasks 表不存在，请先创建表")
                return False
            
            # 根据数据库类型执行不同的 SQL
            if 'sqlite' in db_url.lower():
                # SQLite 使用 VARCHAR，不需要修改
                print("ℹ️  SQLite 数据库：status 字段使用 VARCHAR 类型")
                print("   无需修改表结构，代码已支持 'paused' 状态")
                print("✅ 修复完成（SQLite 无需修改）")
                return True
            
            elif 'mysql' in db_url.lower():
                # MySQL 使用 ENUM，需要修改
                print("检测到 MySQL 数据库")
                print("开始修复 ENUM 字段...")
                print()
                
                # 方法1: 直接修改 ENUM（推荐）
                try:
                    print("尝试方法1: 直接修改 ENUM...")
                    db.session.execute(text("""
                        ALTER TABLE dedup_tasks 
                        MODIFY COLUMN status ENUM('pending', 'running', 'paused', 'completed', 'error', 'cancelled') 
                        NOT NULL DEFAULT 'pending' 
                        COMMENT '任务状态';
                    """))
                    db.session.commit()
                    print("✅ 方法1 成功：ENUM 字段已更新")
                    
                    # 验证
                    result = db.session.execute(text("""
                        SELECT COLUMN_TYPE 
                        FROM INFORMATION_SCHEMA.COLUMNS 
                        WHERE TABLE_SCHEMA = DATABASE() 
                          AND TABLE_NAME = 'dedup_tasks' 
                          AND COLUMN_NAME = 'status';
                    """))
                    row = result.fetchone()
                    if row:
                        print(f"✅ 验证成功：当前 ENUM 定义: {row[0]}")
                        if 'paused' in str(row[0]):
                            print("✅ 'paused' 状态已成功添加到 ENUM")
                            return True
                    
                except Exception as e1:
                    db.session.rollback()
                    error_msg = str(e1).lower()
                    print(f"⚠️  方法1 失败: {str(e1)}")
                    
                    # 方法2: 两步法（先转 VARCHAR，再转回 ENUM）
                    try:
                        print()
                        print("尝试方法2: 两步法修复...")
                        print("  步骤1: 将 status 字段转换为 VARCHAR...")
                        
                        db.session.execute(text("""
                            ALTER TABLE dedup_tasks 
                            MODIFY COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending' 
                            COMMENT '任务状态';
                        """))
                        db.session.commit()
                        print("✅ 步骤1 完成：已转换为 VARCHAR")
                        
                        print("  步骤2: 将 status 字段转换回 ENUM（包含 paused）...")
                        db.session.execute(text("""
                            ALTER TABLE dedup_tasks 
                            MODIFY COLUMN status ENUM('pending', 'running', 'paused', 'completed', 'error', 'cancelled') 
                            NOT NULL DEFAULT 'pending' 
                            COMMENT '任务状态';
                        """))
                        db.session.commit()
                        print("✅ 步骤2 完成：已转换回 ENUM（包含 paused）")
                        
                        # 验证
                        result = db.session.execute(text("""
                            SELECT COLUMN_TYPE 
                            FROM INFORMATION_SCHEMA.COLUMNS 
                            WHERE TABLE_SCHEMA = DATABASE() 
                              AND TABLE_NAME = 'dedup_tasks' 
                              AND COLUMN_NAME = 'status';
                        """))
                        row = result.fetchone()
                        if row:
                            print(f"✅ 验证成功：当前 ENUM 定义: {row[0]}")
                            if 'paused' in str(row[0]):
                                print("✅ 'paused' 状态已成功添加到 ENUM")
                                return True
                        
                    except Exception as e2:
                        db.session.rollback()
                        print(f"❌ 方法2 也失败: {str(e2)}")
                        print()
                        print("=" * 60)
                        print("❌ 修复失败！")
                        print("=" * 60)
                        print()
                        print("请手动执行以下 SQL 语句：")
                        print()
                        print("-- 方法1: 直接修改")
                        print("ALTER TABLE dedup_tasks")
                        print("MODIFY COLUMN status ENUM('pending', 'running', 'paused', 'completed', 'error', 'cancelled')")
                        print("NOT NULL DEFAULT 'pending'")
                        print("COMMENT '任务状态';")
                        print()
                        print("-- 如果方法1失败，使用方法2（两步法）:")
                        print("-- 步骤1:")
                        print("ALTER TABLE dedup_tasks")
                        print("MODIFY COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending'")
                        print("COMMENT '任务状态';")
                        print()
                        print("-- 步骤2:")
                        print("ALTER TABLE dedup_tasks")
                        print("MODIFY COLUMN status ENUM('pending', 'running', 'paused', 'completed', 'error', 'cancelled')")
                        print("NOT NULL DEFAULT 'pending'")
                        print("COMMENT '任务状态';")
                        return False
                
                return True
            
            elif 'postgresql' in db_url.lower() or 'postgres' in db_url.lower():
                # PostgreSQL 使用 VARCHAR，不需要修改
                print("ℹ️  PostgreSQL 数据库：status 字段使用 VARCHAR 类型")
                print("   无需修改表结构，代码已支持 'paused' 状态")
                print("✅ 修复完成（PostgreSQL 无需修改）")
                return True
            
            else:
                print(f"❌ 不支持的数据库类型: {db_url.split('://')[0]}")
                return False
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 修复失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    success = fix_paused_status()
    if success:
        print()
        print("=" * 60)
        print("✅ 修复完成！现在可以正常使用暂停功能了")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("❌ 修复失败，请查看上面的错误信息")
        print("=" * 60)
    sys.exit(0 if success else 1)

