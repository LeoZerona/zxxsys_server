"""在 test 数据库中创建表"""
from flask import Flask
from models import db, User, EmailVerification

def create_tables_in_test_db(database_type='sqlite'):
    """
    在 test 数据库中创建表
    
    参数:
        database_type: 数据库类型 ('sqlite', 'mysql', 'postgresql')
    """
    app = Flask(__name__)
    
    # 根据数据库类型配置连接字符串
    if database_type.lower() == 'sqlite':
        # SQLite: test.db 文件
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        print("使用 SQLite 数据库: test.db")
    
    elif database_type.lower() == 'mysql':
        # MySQL: 需要配置用户名、密码、主机和端口
        import os
        mysql_user = os.environ.get('MYSQL_USER', 'root')
        mysql_password = os.environ.get('MYSQL_PASSWORD', '')
        mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
        mysql_port = os.environ.get('MYSQL_PORT', '3306')
        
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/test?charset=utf8mb4'
        print(f"使用 MySQL 数据库: test")
        print(f"  主机: {mysql_host}:{mysql_port}")
        print(f"  用户: {mysql_user}")
    
    elif database_type.lower() == 'postgresql':
        # PostgreSQL: 需要配置用户名、密码、主机和端口
        import os
        pg_user = os.environ.get('POSTGRES_USER', 'postgres')
        pg_password = os.environ.get('POSTGRES_PASSWORD', '')
        pg_host = os.environ.get('POSTGRES_HOST', 'localhost')
        pg_port = os.environ.get('POSTGRES_PORT', '5432')
        
        app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/test'
        print(f"使用 PostgreSQL 数据库: test")
        print(f"  主机: {pg_host}:{pg_port}")
        print(f"  用户: {pg_user}")
    
    else:
        print(f"不支持的数据库类型: {database_type}")
        print("支持的数据库类型: sqlite, mysql, postgresql")
        return False
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    db.init_app(app)
    
    # 创建表
    with app.app_context():
        try:
            print("\n开始创建表...")
            db.create_all()
            
            # 验证表是否创建成功
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"\n✓ 表创建成功！")
            print(f"\n已创建的表:")
            for table in tables:
                print(f"  - {table}")
            
            # 检查 users 表的列
            if 'users' in tables:
                columns = inspector.get_columns('users')
                print(f"\nusers 表结构:")
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
            
            return True
        
        except Exception as e:
            print(f"\n✗ 创建表失败: {str(e)}")
            print("\n错误详情:")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    import sys
    
    # 从命令行参数获取数据库类型，默认自动检测
    db_type = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not db_type:
        print("=" * 60)
        print("在 test 数据库中创建表")
        print("=" * 60)
        print("\n请选择数据库类型:")
        print("1. SQLite (默认)")
        print("2. MySQL")
        print("3. PostgreSQL")
        
        choice = input("\n请输入选项 (1/2/3) [默认: 1]: ").strip()
        
        if choice == '2':
            db_type = 'mysql'
        elif choice == '3':
            db_type = 'postgresql'
        else:
            db_type = 'sqlite'
    
    print("\n" + "=" * 60)
    success = create_tables_in_test_db(db_type)
    print("=" * 60)
    
    if success:
        print("\n✓ 完成！表已成功创建在 test 数据库中。")
    else:
        print("\n✗ 失败！请检查数据库配置和连接。")
        sys.exit(1)

