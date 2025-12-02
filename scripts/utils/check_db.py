"""检查数据库配置和用户数据"""
from src.app import app, db
from src.models import User

with app.app_context():
    print("=" * 60)
    print("数据库配置检查")
    print("=" * 60)
    print(f"数据库 URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print()
    
    try:
        # 查询所有用户
        users = User.query.all()
        print(f"当前数据库中的用户数量: {len(users)}")
        print()
        
        if users:
            print("用户列表:")
            for user in users:
                print(f"  ID: {user.id}, 邮箱: {user.email}, 角色: {user.role}, 创建时间: {user.created_at}")
        else:
            print("⚠️  数据库中没有用户数据")
        
        print()
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ 查询数据库时出错: {str(e)}")
        import traceback
        traceback.print_exc()

