"""在 test 数据库中创建表的通用脚本"""
from flask import Flask
from models import db, User, EmailVerification

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

def create_tables_in_test():
    """在 test 数据库中创建所有表"""
    app = Flask(__name__)
    
    # 配置数据库
    database_uri = get_database_uri()
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    db.init_app(app)
    
    print("=" * 60)
    print("在 test 数据库中创建表")
    print("=" * 60)
    print(f"\n数据库类型: {DATABASE_TYPE.upper()}")
    print(f"数据库 URI: {database_uri.replace(DATABASE_TYPE.split('+')[0] + '://', '***://') if '+' in DATABASE_TYPE else database_uri}")
    
    # 创建表
    with app.app_context():
        try:
            print("\n正在连接到数据库...")
            
            # 测试连接
            db.engine.connect()
            print("✓ 数据库连接成功")
            
            print("\n开始创建表...")
            db.create_all()
            
            # 验证表是否创建成功
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("\n" + "=" * 60)
            print("✓ 表创建成功！")
            print("=" * 60)
            print(f"\n已创建的表 ({len(tables)} 个):")
            for table in tables:
                print(f"  ✓ {table}")
            
            # 显示表结构
            if 'users' in tables:
                print("\n" + "-" * 60)
                print("users 表结构:")
                print("-" * 60)
                columns = inspector.get_columns('users')
                for col in columns:
                    nullable = "可空" if col.get('nullable', True) else "不可空"
                    unique = " [唯一]" if col.get('unique', False) else ""
                    print(f"  • {col['name']:20s} {str(col['type']):30s} {nullable}{unique}")
            
            if 'email_verifications' in tables:
                print("\n" + "-" * 60)
                print("email_verifications 表结构:")
                print("-" * 60)
                columns = inspector.get_columns('email_verifications')
                for col in columns:
                    nullable = "可空" if col.get('nullable', True) else "不可空"
                    print(f"  • {col['name']:20s} {str(col['type']):30s} {nullable}")
            
            print("\n" + "=" * 60)
            print("✓ 完成！所有表已成功创建在 test 数据库中。")
            print("=" * 60)
            
            return True
        
        except ImportError as e:
            print("\n" + "=" * 60)
            print("✗ 缺少必要的数据库驱动")
            print("=" * 60)
            
            if DATABASE_TYPE.lower() == 'mysql':
                print("\n请安装 MySQL 驱动:")
                print("  pip install pymysql")
            elif DATABASE_TYPE.lower() == 'postgresql':
                print("\n请安装 PostgreSQL 驱动:")
                print("  pip install psycopg2-binary")
            
            print(f"\n详细错误: {str(e)}")
            return False
        
        except Exception as e:
            print("\n" + "=" * 60)
            print("✗ 创建表失败")
            print("=" * 60)
            print(f"\n错误信息: {str(e)}")
            print("\n请检查:")
            print("1. 数据库类型配置是否正确 (DATABASE_TYPE)")
            print("2. 数据库连接配置是否正确 (用户名、密码、主机、端口)")
            print("3. test 数据库是否已创建")
            print("4. 数据库用户是否有创建表的权限")
            print("5. 数据库服务是否正在运行")
            
            import traceback
            print("\n详细错误信息:")
            traceback.print_exc()
            
            return False

if __name__ == '__main__':
    success = create_tables_in_test()
    
    if not success:
        print("\n提示:")
        print("1. 如果是 MySQL，请修改脚本中的 DATABASE_TYPE = 'mysql' 和 MYSQL_CONFIG")
        print("2. 如果是 PostgreSQL，请修改脚本中的 DATABASE_TYPE = 'postgresql' 和 POSTGRESQL_CONFIG")
        print("3. 如果是 SQLite，确保脚本中的 DATABASE_TYPE = 'sqlite'")
        exit(1)

