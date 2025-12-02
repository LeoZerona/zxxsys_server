"""
查询数据库中用户表的详细数据
"""
from src.app import app, db
from src.models import User
from datetime import datetime

with app.app_context():
    print("="*80)
    print("📊 数据库用户表查询结果")
    print("="*80)
    print(f"⏰ 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 数据库 URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print()
    
    try:
        # 查询所有用户
        users = User.query.order_by(User.id.asc()).all()
        total_count = len(users)
        
        print(f"📈 当前用户总数: {total_count}")
        print()
        
        if users:
            print("="*80)
            print("用户详细信息列表")
            print("="*80)
            
            for i, user in enumerate(users, 1):
                print(f"\n【用户 {i}】")
                print(f"   ID: {user.id}")
                print(f"   邮箱: {user.email}")
                print(f"   角色: {user.role}")
                print(f"   创建时间: {user.created_at}")
                print(f"   更新时间: {user.updated_at}")
                print(f"   是否激活: {'是' if user.is_active else '否'}")
                print(f"   密码哈希: {user.password_hash[:60]}...")
                print("-" * 80)
            
            print()
            print("="*80)
            print("📊 统计信息")
            print("="*80)
            
            # 按角色统计
            role_counts = {}
            for user in users:
                role_counts[user.role] = role_counts.get(user.role, 0) + 1
            
            print(f"按角色统计:")
            for role, count in role_counts.items():
                print(f"   - {role}: {count} 人")
            
            print()
            print(f"激活状态统计:")
            active_count = sum(1 for u in users if u.is_active)
            inactive_count = total_count - active_count
            print(f"   - 已激活: {active_count} 人")
            print(f"   - 未激活: {inactive_count} 人")
            
            print()
            print(f"时间范围:")
            if users:
                oldest = min(users, key=lambda u: u.created_at)
                newest = max(users, key=lambda u: u.created_at)
                print(f"   - 最早注册: {oldest.created_at} ({oldest.email})")
                print(f"   - 最新注册: {newest.created_at} ({newest.email})")
            
        else:
            print("⚠️  数据库中没有用户数据")
        
        print()
        print("="*80)
        
    except Exception as e:
        print(f"❌ 查询数据库时出错: {str(e)}")
        import traceback
        traceback.print_exc()

