"""在 test 数据库中重建 users 表"""
from flask import Flask
from models import db, User
from sqlalchemy import inspect

# ============================================================================
# 数据库配置 - 请根据你的实际情况修改
# ============================================================================

# 数据库类型: 'sqlite', 'mysql', 'postgresql'
DATABASE_TYPE = 'sqlite'  # 请修改为你使用的数据库类型

# MySQL 配置（如果使用 MySQL）
MYSQL_CONFIG = {
    'user': 'root',
    'password': '',  # 请填写你的 MySQL 密码
    'host': 'localhost',
    'port': '3306'
}

# PostgreSQL 配置（如果使用 PostgreSQL）
POSTGRESQL_CONFIG = {
    'user': 'postgres',
    'password': '',  # 请填写你的 PostgreSQL 密码
    'host': 'localhost',
    'port': '5432'
}

# ============================================================================

def get_database_uri():
    """根据数据库类型生成数据库连接 URI"""
    if DATABASE_TYPE.lower() == 'sqlite':
        return 'sqlite:///test.db'
    
    elif DATABASE_TYPE.lower() == 'mysql':
        user = MYSQL_CONFIG['user']
        password = MYSQL_CONFIG['password']
        host = MYSQL_CONFIG['host']
        port = MYSQL_CONFIG['port']
        
        if not password:
            print("警告: MySQL 密码为空，请修改 MYSQL_CONFIG 中的密码")
        
        return f'mysql+pymysql://{user}:{password}@{host}:{port}/test?charset=utf8mb4'
    
    elif DATABASE_TYPE.lower() == 'postgresql':
        user = POSTGRESQL_CONFIG['user']
        password = POSTGRESQL_CONFIG['password']
        host = POSTGRESQL_CONFIG['host']
        port = POSTGRESQL_CONFIG['port']
        
        if not password:
            print("警告: PostgreSQL 密码为空，请修改 POSTGRESQL_CONFIG 中的密码")
        
        return f'postgresql://{user}:{password}@{host}:{port}/test'
    
    else:
        raise ValueError(f"不支持的数据库类型: {DATABASE_TYPE}")

def rebuild_users_table_in_test():
    """在 test 数据库中重建 users 表"""
    app = Flask(__name__)
    
    # 设置数据库连接
    database_uri = get_database_uri()
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    db.init_app(app)
    
    with app.app_context():
        try:
            print("=" * 60)
            print("在 test 数据库中重建 users 表")
            print("=" * 60)
            print(f"数据库类型: {DATABASE_TYPE}")
            print(f"数据库 URI: {database_uri}")
            print()
            
            # 检查表是否存在
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"当前数据库中的表: {tables}")
            print()
            
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
            
            # 验证表结构
            columns = inspector.get_columns('users')
            print("表结构验证:")
            for col in columns:
                nullable = "NULL" if col.get('nullable') else "NOT NULL"
                default = f" DEFAULT {col.get('default')}" if col.get('default') is not None else ""
                print(f"  - {col['name']}: {col['type']} {nullable}{default}")
            
            # 检查索引
            print()
            print("索引验证:")
            indexes = inspector.get_indexes('users')
            for idx in indexes:
                print(f"  - {idx['name']}: {', '.join(idx['column_names'])}")
            
            print()
            print("=" * 60)
            print("✅ 重建完成！")
            print("=" * 60)
            print()
            print("表结构说明:")
            print("- id: 主键，自增")
            print("- email: 邮箱地址，唯一，已建立索引")
            print("- password_hash: 密码哈希值")
            print("- role: 用户权限（'super_admin', 'admin', 'user'），默认 'user'，已建立索引")
            print("- created_at: 创建时间")
            print("- updated_at: 更新时间")
            print("- is_active: 是否激活")
            
            return True
        
        except Exception as e:
            print(f"\n❌ 重建失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("\n⚠️  警告：此操作将在 test 数据库中删除并重建 users 表！")
    print("   确保 users 表是空表或数据已备份。")
    print()
    print(f"当前配置:")
    print(f"  数据库类型: {DATABASE_TYPE}")
    if DATABASE_TYPE.lower() == 'mysql':
        print(f"  MySQL 配置: {MYSQL_CONFIG}")
    elif DATABASE_TYPE.lower() == 'postgresql':
        print(f"  PostgreSQL 配置: {POSTGRESQL_CONFIG}")
    print()
    
    confirm = input("确认继续？(yes/no): ").strip().lower()
    
    if confirm == 'yes':
        rebuild_users_table_in_test()
    else:
        print("操作已取消")

