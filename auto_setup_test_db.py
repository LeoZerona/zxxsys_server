"""自动在 test 数据库中创建表（交互式）"""
from flask import Flask
from models import db, User, EmailVerification

def create_tables_interactive():
    """交互式创建表"""
    print("=" * 60)
    print("在 test 数据库中创建表")
    print("=" * 60)
    
    # 选择数据库类型
    print("\n请选择数据库类型:")
    print("1. SQLite (test.db 文件)")
    print("2. MySQL")
    print("3. PostgreSQL")
    
    choice = input("\n请输入选项 (1/2/3) [默认: 1]: ").strip()
    
    if choice == '2':
        db_type = 'mysql'
    elif choice == '3':
        db_type = 'postgresql'
    else:
        db_type = 'sqlite'
    
    app = Flask(__name__)
    
    # 配置数据库连接
    if db_type == 'sqlite':
        database_uri = 'sqlite:///test.db'
        print(f"\n使用 SQLite 数据库: test.db")
    
    elif db_type == 'mysql':
        print("\n请输入 MySQL 配置:")
        user = input("用户名 [默认: root]: ").strip() or 'root'
        password = input("密码: ").strip()
        host = input("主机 [默认: localhost]: ").strip() or 'localhost'
        port = input("端口 [默认: 3306]: ").strip() or '3306'
        
        database_uri = f'mysql+pymysql://{user}:{password}@{host}:{port}/test?charset=utf8mb4'
        
        print(f"\n使用 MySQL 数据库: test")
        print(f"  主机: {host}:{port}")
        print(f"  用户: {user}")
    
    elif db_type == 'postgresql':
        print("\n请输入 PostgreSQL 配置:")
        user = input("用户名 [默认: postgres]: ").strip() or 'postgres'
        password = input("密码: ").strip()
        host = input("主机 [默认: localhost]: ").strip() or 'localhost'
        port = input("端口 [默认: 5432]: ").strip() or '5432'
        
        database_uri = f'postgresql://{user}:{password}@{host}:{port}/test'
        
        print(f"\n使用 PostgreSQL 数据库: test")
        print(f"  主机: {host}:{port}")
        print(f"  用户: {user}")
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    db.init_app(app)
    
    # 创建表
    with app.app_context():
        try:
            print("\n正在连接到数据库...")
            
            # 测试连接
            connection = db.engine.connect()
            connection.close()
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
            
            # 显示 users 表结构
            if 'users' in tables:
                print("\n" + "-" * 60)
                print("users 表结构:")
                print("-" * 60)
                columns = inspector.get_columns('users')
                for col in columns:
                    nullable = "可空" if col.get('nullable', True) else "不可空"
                    unique = " [唯一]" if col.get('unique', False) else ""
                    default = f" [默认: {col.get('default', '无')}]" if col.get('default') else ""
                    print(f"  • {col['name']:20s} {str(col['type']):30s} {nullable}{unique}{default}")
            
            print("\n" + "=" * 60)
            print("✓ 完成！所有表已成功创建在 test 数据库中。")
            print("=" * 60)
            
            return True
        
        except ImportError as e:
            print("\n" + "=" * 60)
            print("✗ 缺少必要的数据库驱动")
            print("=" * 60)
            
            if db_type == 'mysql':
                print("\n请安装 MySQL 驱动:")
                print("  pip install pymysql")
            elif db_type == 'postgresql':
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
            print("1. 数据库连接配置是否正确")
            print("2. test 数据库是否已创建")
            print("3. 数据库用户是否有创建表的权限")
            print("4. 数据库服务是否正在运行")
            
            import traceback
            print("\n详细错误信息:")
            traceback.print_exc()
            
            return False

if __name__ == '__main__':
    success = create_tables_interactive()
    
    if not success:
        exit(1)

