"""
数据库迁移脚本：为 dedup_tasks 表的 status 字段添加 'paused' 状态支持
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db
from sqlalchemy import text, inspect


def check_status_enum_values(table_name, column_name):
    """检查 ENUM 字段的当前值（仅适用于 MySQL）"""
    inspector = inspect(db.engine)
    columns = inspector.get_columns(table_name)
    
    for col in columns:
        if col['name'] == column_name:
            col_type = str(col['type'])
            # 提取 ENUM 值
            if 'ENUM' in col_type.upper():
                # 解析 ENUM('value1', 'value2', ...)
                import re
                match = re.search(r"ENUM\((.+)\)", col_type, re.IGNORECASE)
                if match:
                    values_str = match.group(1)
                    # 提取引号内的值
                    values = re.findall(r"'([^']+)'", values_str)
                    return values
            return None
    return None


def migrate_add_paused_status():
    """为 status 字段添加 'paused' 状态支持"""
    with app.app_context():
        try:
            # 检测数据库类型
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            
            print("=" * 60)
            print("数据库迁移：为 dedup_tasks 表添加 'paused' 状态支持")
            print("=" * 60)
            print(f"数据库类型: {db_url.split('://')[0]}")
            print()
            
            # 检查表是否存在
            inspector = inspect(db.engine)
            if 'dedup_tasks' not in inspector.get_table_names():
                print("❌ 错误：dedup_tasks 表不存在，请先创建表")
                return False
            
            # 根据数据库类型执行不同的 SQL
            if 'sqlite' in db_url.lower():
                # SQLite 使用 VARCHAR，不需要修改表结构
                # 只需要确保代码中支持 'paused' 状态即可
                print("ℹ️  SQLite 数据库：status 字段使用 VARCHAR 类型")
                print("   无需修改表结构，代码已支持 'paused' 状态")
                print("✅ 迁移完成（SQLite 无需修改）")
                return True
            
            elif 'mysql' in db_url.lower():
                # MySQL 使用 ENUM，需要修改 ENUM 定义
                print("检测当前 status 字段的 ENUM 值...")
                current_values = check_status_enum_values('dedup_tasks', 'status')
                
                if current_values:
                    print(f"   当前 ENUM 值: {', '.join(current_values)}")
                    
                    if 'paused' in current_values:
                        print("✅ 'paused' 状态已存在，无需迁移")
                        return True
                    
                    print("\n开始更新 ENUM 定义...")
                    print("   添加 'paused' 状态到 ENUM...")
                    
                    # 构建新的 ENUM 值列表
                    new_values = list(current_values)
                    if 'paused' not in new_values:
                        # 在 'running' 之后插入 'paused'
                        if 'running' in new_values:
                            idx = new_values.index('running')
                            new_values.insert(idx + 1, 'paused')
                        else:
                            # 如果没有 'running'，添加到列表末尾
                            new_values.append('paused')
                    
                    enum_values_str = "', '".join(new_values)
                    enum_sql = f"ENUM('{enum_values_str}')"
                    
                    # 执行 ALTER TABLE MODIFY
                    try:
                        db.session.execute(text(f"""
                            ALTER TABLE dedup_tasks 
                            MODIFY COLUMN status {enum_sql} 
                            NOT NULL DEFAULT 'pending' 
                            COMMENT '任务状态';
                        """))
                        db.session.commit()
                        print("✅ ENUM 定义更新成功")
                        
                        # 验证更新
                        updated_values = check_status_enum_values('dedup_tasks', 'status')
                        if updated_values and 'paused' in updated_values:
                            print(f"✅ 验证成功：当前 ENUM 值包含 'paused'")
                            print(f"   当前 ENUM 值: {', '.join(updated_values)}")
                        else:
                            print("⚠️  警告：验证失败，但 SQL 执行成功")
                        
                        return True
                    except Exception as e:
                        db.session.rollback()
                        error_msg = str(e).lower()
                        
                        # 如果 ALTER TABLE MODIFY 失败，尝试先转换为 VARCHAR，再转回 ENUM
                        if 'modify' in error_msg or 'enum' in error_msg:
                            print("⚠️  直接修改 ENUM 失败，尝试两步法...")
                            print("   步骤 1: 将 status 字段转换为 VARCHAR...")
                            
                            try:
                                # 步骤 1: 转换为 VARCHAR
                                db.session.execute(text("""
                                    ALTER TABLE dedup_tasks 
                                    MODIFY COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending' 
                                    COMMENT '任务状态';
                                """))
                                db.session.commit()
                                print("✅ 步骤 1 完成：已转换为 VARCHAR")
                                
                                # 步骤 2: 转换回 ENUM（包含 paused）
                                print("   步骤 2: 将 status 字段转换回 ENUM（包含 paused）...")
                                db.session.execute(text(f"""
                                    ALTER TABLE dedup_tasks 
                                    MODIFY COLUMN status {enum_sql} 
                                    NOT NULL DEFAULT 'pending' 
                                    COMMENT '任务状态';
                                """))
                                db.session.commit()
                                print("✅ 步骤 2 完成：已转换回 ENUM（包含 paused）")
                                
                                # 验证更新
                                updated_values = check_status_enum_values('dedup_tasks', 'status')
                                if updated_values and 'paused' in updated_values:
                                    print(f"✅ 验证成功：当前 ENUM 值包含 'paused'")
                                    print(f"   当前 ENUM 值: {', '.join(updated_values)}")
                                else:
                                    print("⚠️  警告：验证失败，但 SQL 执行成功")
                                
                                return True
                            except Exception as e2:
                                db.session.rollback()
                                print(f"❌ 两步法也失败: {str(e2)}")
                                raise e2
                        else:
                            raise e
                else:
                    print("⚠️  无法检测当前 ENUM 值，尝试直接更新...")
                    # 直接尝试更新为包含 paused 的 ENUM
                    enum_sql = "ENUM('pending', 'running', 'paused', 'completed', 'error', 'cancelled')"
                    try:
                        db.session.execute(text(f"""
                            ALTER TABLE dedup_tasks 
                            MODIFY COLUMN status {enum_sql} 
                            NOT NULL DEFAULT 'pending' 
                            COMMENT '任务状态';
                        """))
                        db.session.commit()
                        print("✅ ENUM 定义更新成功")
                        return True
                    except Exception as e:
                        db.session.rollback()
                        raise e
            
            elif 'postgresql' in db_url.lower() or 'postgres' in db_url.lower():
                # PostgreSQL 使用 VARCHAR 或 CHECK 约束，通常不需要修改
                print("ℹ️  PostgreSQL 数据库：status 字段通常使用 VARCHAR 类型")
                print("   无需修改表结构，代码已支持 'paused' 状态")
                print("✅ 迁移完成（PostgreSQL 无需修改）")
                return True
            
            else:
                print(f"❌ 不支持的数据库类型: {db_url.split('://')[0]}")
                return False
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    success = migrate_add_paused_status()
    sys.exit(0 if success else 1)

