"""
测试 MySQL 数据库连接
"""
from src.app import app, db
from src.models import User

with app.app_context():
    print("="*80)
    print("🔍 测试 MySQL 数据库连接")
    print("="*80)
    print(f"数据库 URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print()
    
    try:
        # 测试数据库连接
        with db.engine.connect() as conn:
            result = conn.execute(db.text("SELECT DATABASE(), USER()"))
            db_info = result.fetchone()
            if db_info:
                current_db = db_info[0]
                current_user = db_info[1]
                print(f"✅ 数据库连接成功!")
                print(f"   当前数据库: {current_db}")
                print(f"   当前用户: {current_user}")
            
            # 检查表是否存在
            result = conn.execute(db.text("SHOW TABLES LIKE 'users'"))
            table_exists = result.fetchone()
            if table_exists:
                print(f"✅ users 表存在")
                
                # 查询用户数量
                user_count = User.query.count()
                print(f"📊 当前用户数量: {user_count}")
            else:
                print(f"⚠️  users 表不存在，需要创建")
        
        print()
        print("="*80)
        
    except Exception as e:
        print(f"❌ 连接数据库时出错: {str(e)}")
        print()
        print("💡 可能的原因:")
        print("   1. MySQL 服务未启动")
        print("   2. 数据库连接信息不正确")
        print("   3. test 数据库不存在")
        print("   4. 用户权限不足")
        import traceback
        traceback.print_exc()

