"""
查询 MySQL test 数据库中的 users 表数据
"""
from flask import Flask
from src.models import db, User
from datetime import datetime

# 创建 Flask 应用实例（使用 MySQL test 数据库）
app = Flask(__name__)

# 配置 MySQL test 数据库（与 create_users_table.py 保持一致）
mysql_user = 'root'
mysql_password = '123456'  # 请根据你的实际情况修改
mysql_host = 'localhost'
mysql_port = '3306'

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/test?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

with app.app_context():
    print("="*80)
    print("📊 MySQL test 数据库 - 用户表查询结果")
    print("="*80)
    print(f"⏰ 查询时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 数据库: MySQL")
    print(f"📊 数据库名: test")
    print(f"🔗 连接: {mysql_user}@{mysql_host}:{mysql_port}")
    print()
    
    try:
        # 测试数据库连接
        with db.engine.connect() as conn:
            result = conn.execute(db.text("SELECT DATABASE()"))
            current_db = result.scalar()
            print(f"✅ 数据库连接成功!")
            print(f"   当前数据库: {current_db}")
        
        # 查询所有用户
        users = User.query.order_by(User.id.asc()).all()
        total_count = len(users)
        
        print()
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
            print("⚠️  MySQL test 数据库的 users 表中没有用户数据")
            print()
            print("💡 提示:")
            print("   - 如果之前注册的用户数据在 SQLite 数据库中，需要重新注册")
            print("   - 或者需要将 SQLite 中的数据迁移到 MySQL")
        
        print()
        print("="*80)
        
    except Exception as e:
        print(f"❌ 连接或查询数据库时出错: {str(e)}")
        print()
        print("💡 可能的原因:")
        print("   1. MySQL 服务未启动")
        print("   2. 数据库连接信息不正确（用户名、密码、主机、端口）")
        print("   3. test 数据库不存在")
        print("   4. users 表不存在")
        print()
        print("🔧 解决方法:")
        print("   1. 检查 MySQL 服务是否运行")
        print("   2. 检查数据库连接信息是否正确")
        print("   3. 确认 test 数据库已创建")
        print("   4. 如果 users 表不存在，运行: python create_users_table.py")
        import traceback
        traceback.print_exc()

