"""直接生成 users 表的脚本"""
from flask import Flask
from models import db, User
from sqlalchemy import inspect, text

# ============================================================================
# 数据库配置 - 请根据实际情况修改
# ============================================================================

# 方式 1: 直接指定数据库连接字符串（推荐）
DATABASE_URI = None  # 如果为 None，将使用下面的配置

# 方式 2: 使用配置（如果 DATABASE_URI 为 None）
DATABASE_TYPE = 'mysql'  # 'sqlite', 'mysql', 'postgresql'

# MySQL 配置
MYSQL_CONFIG = {
    'user': 'root',
    'password': '123456',  # 修改为你的密码
    'host': 'localhost',
    'port': '3306',
    'database': 'test'
}

# PostgreSQL 配置
POSTGRESQL_CONFIG = {
    'user': 'postgres',
    'password': '',  # 修改为你的密码
    'host': 'localhost',
    'port': '5432',
    'database': 'test'
}

# ============================================================================

def get_database_uri():
    """获取数据库连接 URI"""
    # 如果直接指定了 URI，使用它
    if DATABASE_URI:
        return DATABASE_URI
    
    # 否则根据类型生成
    if DATABASE_TYPE.lower() == 'sqlite':
        return 'sqlite:///test.db'
    
    elif DATABASE_TYPE.lower() == 'mysql':
        user = MYSQL_CONFIG['user']
        password = MYSQL_CONFIG['password']
        host = MYSQL_CONFIG['host']
        port = MYSQL_CONFIG['port']
        database = MYSQL_CONFIG['database']
        return f'mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4'
    
    elif DATABASE_TYPE.lower() == 'postgresql':
        user = POSTGRESQL_CONFIG['user']
        password = POSTGRESQL_CONFIG['password']
        host = POSTGRESQL_CONFIG['host']
        port = POSTGRESQL_CONFIG['port']
        database = POSTGRESQL_CONFIG['database']
        return f'postgresql://{user}:{password}@{host}:{port}/{database}'
    
    else:
        raise ValueError(f"不支持的数据库类型: {DATABASE_TYPE}")

def create_users_table():
    """创建 users 表"""
    app = Flask(__name__)
    
    # 设置数据库连接
    database_uri = get_database_uri()
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    db.init_app(app)
    
    with app.app_context():
        try:
            print("=" * 70)
            print("生成 users 表")
            print("=" * 70)
            print()
            
            # 显示数据库信息
            print(f"数据库类型: {DATABASE_TYPE.upper()}")
            if 'mysql' in database_uri:
                # 隐藏密码显示
                safe_uri = database_uri.split('@')[1] if '@' in database_uri else database_uri
                print(f"数据库: {safe_uri}")
            elif 'postgresql' in database_uri:
                safe_uri = database_uri.split('@')[1] if '@' in database_uri else database_uri
                print(f"数据库: {safe_uri}")
            else:
                print(f"数据库文件: {database_uri.replace('sqlite:///', '')}")
            print()
            
            # 检查表是否已存在
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'users' in tables:
                print("⚠️  users 表已存在")
                print()
                print("请选择操作:")
                print("  1. 删除现有表并重新创建（会丢失所有数据）")
                print("  2. 仅添加缺失的字段（保留数据）")
                print("  3. 取消")
                print()
                choice = input("请输入选择 (1/2/3): ").strip()
                
                if choice == '1':
                    print()
                    print("正在删除现有的 users 表...")
                    User.__table__.drop(db.engine, checkfirst=True)
                    print("✅ users 表已删除")
                    print()
                    print("正在创建新的 users 表...")
                    User.__table__.create(db.engine, checkfirst=True)
                    print("✅ users 表创建成功")
                
                elif choice == '2':
                    print()
                    print("正在检查并添加缺失的字段...")
                    # 获取现有字段
                    existing_columns = [col['name'] for col in inspector.get_columns('users')]
                    
                    # 检查是否需要添加 role 字段
                    if 'role' not in existing_columns:
                        print("  检测到缺少 role 字段，正在添加...")
                        if DATABASE_TYPE.lower() == 'sqlite':
                            db.session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL;"))
                        elif DATABASE_TYPE.lower() == 'mysql':
                            db.session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user' AFTER password_hash;"))
                        elif DATABASE_TYPE.lower() == 'postgresql':
                            db.session.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user';"))
                        
                        # 更新现有用户的 role
                        db.session.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';"))
                        db.session.commit()
                        print("  ✅ role 字段已添加")
                    else:
                        print("  ✅ 所有字段已存在")
                    
                    # 检查并创建索引
                    indexes = [idx['name'] for idx in inspector.get_indexes('users')]
                    if 'idx_users_role' not in indexes:
                        print("  正在创建 role 字段索引...")
                        db.session.execute(text("CREATE INDEX idx_users_role ON users(role);"))
                        db.session.commit()
                        print("  ✅ 索引已创建")
                    else:
                        print("  ✅ 索引已存在")
                    
                    print()
                    print("✅ 字段更新完成")
                
                else:
                    print("操作已取消")
                    return False
            else:
                print("users 表不存在，正在创建...")
                print()
                # 创建表
                User.__table__.create(db.engine, checkfirst=True)
                print("✅ users 表创建成功")
            
            print()
            print("-" * 70)
            print("表结构信息")
            print("-" * 70)
            
            # 显示表结构
            columns = inspector.get_columns('users')
            print("\n字段列表:")
            for col in columns:
                nullable = "NULL" if col.get('nullable') else "NOT NULL"
                default = ""
                if col.get('default') is not None:
                    default_val = str(col.get('default'))
                    default = f" DEFAULT {default_val}"
                print(f"  • {col['name']:20s} {str(col['type']):30s} {nullable}{default}")
            
            # 显示索引
            print("\n索引列表:")
            indexes = inspector.get_indexes('users')
            if indexes:
                for idx in indexes:
                    unique = " [UNIQUE]" if idx.get('unique') else ""
                    print(f"  • {idx['name']:20s} 列: {', '.join(idx['column_names'])}{unique}")
            else:
                print("  无索引")
            
            print()
            print("=" * 70)
            print("✅ 完成！users 表已就绪")
            print("=" * 70)
            print()
            print("表包含以下字段:")
            print("  - id: 主键，自增")
            print("  - email: 邮箱地址，唯一，已建立索引")
            print("  - password_hash: 密码哈希值")
            print("  - role: 用户权限（'super_admin', 'admin', 'user'），默认 'user'，已建立索引")
            print("  - created_at: 创建时间")
            print("  - updated_at: 更新时间")
            print("  - is_active: 是否激活")
            
            return True
        
        except Exception as e:
            print()
            print("=" * 70)
            print("❌ 操作失败")
            print("=" * 70)
            print(f"\n错误信息: {str(e)}")
            print()
            print("请检查:")
            print("  1. 数据库配置是否正确（用户名、密码、主机、端口）")
            print("  2. 数据库是否存在（如 test 数据库）")
            print("  3. 数据库服务是否正在运行")
            print("  4. 数据库驱动是否已安装")
            print("     - MySQL: pip install pymysql")
            print("     - PostgreSQL: pip install psycopg2-binary")
            
            import traceback
            print("\n详细错误信息:")
            traceback.print_exc()
            return False

if __name__ == '__main__':
    # 如果使用 MySQL，可以直接在这里修改连接字符串（更简单）
    DATABASE_URI = 'mysql+pymysql://root:123456@localhost:3306/test?charset=utf8mb4'
    
    # 如果使用 PostgreSQL，可以直接在这里修改连接字符串
    # DATABASE_URI = 'postgresql://postgres:password@localhost:5432/test'
    
    # 如果使用 SQLite，可以直接在这里修改连接字符串
    # DATABASE_URI = 'sqlite:///test.db'
    
    create_users_table()

