"""在 test 数据库中创建表（简化版，直接配置）"""
from flask import Flask
from models import db, User, EmailVerification

def create_tables():
    """在 test 数据库中创建表"""
    app = Flask(__name__)
    
    # ============================================================
    # 请根据你的数据库类型修改下面的配置
    # ============================================================
    
    # 方式 1: SQLite (如果是 SQLite 的 test.db 文件)
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    
    # 方式 2: MySQL (取消下面的注释并修改配置)
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://用户名:密码@localhost:3306/test?charset=utf8mb4'
    # 例如: app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:123456@localhost:3306/test?charset=utf8mb4'
    
    # 方式 3: PostgreSQL (取消下面的注释并修改配置)
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://用户名:密码@localhost:5432/test'
    # 例如: app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:123456@localhost:5432/test'
    
    # ============================================================
    # 默认配置（如果上面没有配置，会使用这个）
    # 请修改为你实际的数据库连接字符串
    # ============================================================
    
    # 如果你使用 MySQL，取消下面这行的注释并修改：
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:你的密码@localhost:3306/test?charset=utf8mb4'
    
    # 如果你使用 PostgreSQL，取消下面这行的注释并修改：
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:你的密码@localhost:5432/test'
    
    # 如果你使用 SQLite，使用这个：
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    db.init_app(app)
    
    # 创建表
    with app.app_context():
        try:
            print("正在连接到 test 数据库...")
            print(f"数据库 URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
            print("\n开始创建表...")
            
            db.create_all()
            
            # 验证表是否创建成功
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("\n" + "=" * 60)
            print("✓ 表创建成功！")
            print("=" * 60)
            print(f"\n已创建的表: {', '.join(tables)}")
            
            # 检查 users 表的列
            if 'users' in tables:
                columns = inspector.get_columns('users')
                print(f"\nusers 表结构:")
                for col in columns:
                    nullable = "可空" if col.get('nullable') else "不可空"
                    print(f"  - {col['name']:20s} {str(col['type']):30s} ({nullable})")
            
            if 'email_verifications' in tables:
                columns = inspector.get_columns('email_verifications')
                print(f"\nemail_verifications 表结构:")
                for col in columns:
                    nullable = "可空" if col.get('nullable') else "不可空"
                    print(f"  - {col['name']:20s} {str(col['type']):30s} ({nullable})")
            
            print("\n" + "=" * 60)
            print("✓ 完成！所有表已成功创建在 test 数据库中。")
            print("=" * 60)
            
            return True
        
        except Exception as e:
            print("\n" + "=" * 60)
            print("✗ 创建表失败")
            print("=" * 60)
            print(f"\n错误信息: {str(e)}")
            print("\n请检查:")
            print("1. 数据库连接配置是否正确")
            print("2. test 数据库是否存在")
            print("3. 数据库用户是否有创建表的权限")
            print("4. 是否需要安装数据库驱动 (MySQL: pip install pymysql, PostgreSQL: pip install psycopg2)")
            
            import traceback
            print("\n详细错误信息:")
            traceback.print_exc()
            
            return False

if __name__ == '__main__':
    create_tables()

