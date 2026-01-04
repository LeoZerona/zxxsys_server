"""
数据库迁移脚本：为 dedup_tasks 表添加新字段
添加 analysis_type（分析类型）和 estimated_duration（预估时长）字段
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.app import app, db
from sqlalchemy import text, inspect


def check_column_exists(table_name, column_name):
    """检查字段是否已存在"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def migrate_add_dedup_task_fields():
    """添加去重任务表的新字段"""
    with app.app_context():
        try:
            # 检测数据库类型
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            
            print("=" * 60)
            print("数据库迁移：为 dedup_tasks 表添加新字段")
            print("=" * 60)
            print(f"数据库类型: {db_url.split('://')[0]}")
            print()
            
            # 检查表是否存在
            inspector = inspect(db.engine)
            if 'dedup_tasks' not in inspector.get_table_names():
                print("❌ 错误：dedup_tasks 表不存在，请先创建表")
                return False
            
            # 检查字段是否已存在
            has_analysis_type = check_column_exists('dedup_tasks', 'analysis_type')
            has_estimated_duration = check_column_exists('dedup_tasks', 'estimated_duration')
            
            if has_analysis_type and has_estimated_duration:
                print("ℹ️  字段已存在，跳过迁移")
                print("   - analysis_type: ✅")
                print("   - estimated_duration: ✅")
                return True
            
            print("开始添加字段...")
            print()
            
            # 根据数据库类型执行不同的 SQL
            if 'sqlite' in db_url.lower():
                # SQLite
                if not has_analysis_type:
                    print("添加 analysis_type 字段...")
                    db.session.execute(text("""
                        ALTER TABLE dedup_tasks 
                        ADD COLUMN analysis_type VARCHAR(50) DEFAULT 'full';
                    """))
                    print("✅ analysis_type 字段添加成功")
                
                if not has_estimated_duration:
                    print("添加 estimated_duration 字段...")
                    db.session.execute(text("""
                        ALTER TABLE dedup_tasks 
                        ADD COLUMN estimated_duration INTEGER;
                    """))
                    print("✅ estimated_duration 字段添加成功")
            
            elif 'mysql' in db_url.lower():
                # MySQL
                if not has_analysis_type:
                    print("添加 analysis_type 字段...")
                    db.session.execute(text("""
                        ALTER TABLE dedup_tasks 
                        ADD COLUMN analysis_type VARCHAR(50) DEFAULT 'full' 
                        COMMENT '分析类型：full=全量分析, incremental=增量分析, custom=自定义分析' 
                        AFTER config_json;
                    """))
                    print("✅ analysis_type 字段添加成功")
                
                if not has_estimated_duration:
                    print("添加 estimated_duration 字段...")
                    db.session.execute(text("""
                        ALTER TABLE dedup_tasks 
                        ADD COLUMN estimated_duration INT 
                        COMMENT '预估时长（秒）' 
                        AFTER analysis_type;
                    """))
                    print("✅ estimated_duration 字段添加成功")
            
            elif 'postgresql' in db_url.lower() or 'postgres' in db_url.lower():
                # PostgreSQL
                if not has_analysis_type:
                    print("添加 analysis_type 字段...")
                    db.session.execute(text("""
                        ALTER TABLE dedup_tasks 
                        ADD COLUMN IF NOT EXISTS analysis_type VARCHAR(50) DEFAULT 'full';
                    """))
                    print("✅ analysis_type 字段添加成功")
                
                if not has_estimated_duration:
                    print("添加 estimated_duration 字段...")
                    db.session.execute(text("""
                        ALTER TABLE dedup_tasks 
                        ADD COLUMN IF NOT EXISTS estimated_duration INTEGER;
                    """))
                    print("✅ estimated_duration 字段添加成功")
            
            else:
                print(f"❌ 不支持的数据库类型: {db_url.split('://')[0]}")
                return False
            
            # 提交更改
            db.session.commit()
            print()
            print("=" * 60)
            print("✅ 数据库迁移成功！")
            print("=" * 60)
            
            # 验证字段
            print()
            print("验证字段...")
            has_analysis_type = check_column_exists('dedup_tasks', 'analysis_type')
            has_estimated_duration = check_column_exists('dedup_tasks', 'estimated_duration')
            
            if has_analysis_type:
                print("✅ analysis_type 字段存在")
            else:
                print("❌ analysis_type 字段不存在")
            
            if has_estimated_duration:
                print("✅ estimated_duration 字段存在")
            else:
                print("❌ estimated_duration 字段不存在")
            
            return True
        
        except Exception as e:
            db.session.rollback()
            error_msg = str(e).lower()
            
            if 'duplicate column name' in error_msg or 'already exists' in error_msg:
                print("ℹ️  字段已存在，跳过迁移")
                return True
            else:
                print(f"❌ 迁移失败: {str(e)}")
                import traceback
                traceback.print_exc()
                return False


if __name__ == '__main__':
    success = migrate_add_dedup_task_fields()
    sys.exit(0 if success else 1)

