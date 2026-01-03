"""数据库迁移脚本：添加用户权限字段"""
from src.app import app, db
from src.models import User

def migrate_add_role():
    """添加用户权限字段"""
    with app.app_context():
        try:
            # 检查字段是否已存在（通过尝试查询）
            try:
                # 尝试查询 role 字段
                User.query.with_entities(User.role).first()
                print("✓ role 字段已存在")
            except Exception:
                # 如果字段不存在，需要手动添加（SQLite 不支持直接 ALTER ADD COLUMN）
                print("⚠️  检测到 role 字段可能不存在")
                print("   对于 SQLite，需要手动执行 SQL 或重新创建表")
                print("\n执行以下 SQL 添加字段：")
                print("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL;")
                print("\n或者重新创建表（会丢失数据）：")
                print("python init_db.py")
                return False
            
            # 更新现有用户的权限（如果没有设置）
            users_without_role = User.query.filter(
                (User.role == None) | (User.role == '')
            ).all()
            
            if users_without_role:
                print(f"\n找到 {len(users_without_role)} 个用户需要设置默认权限...")
                for user in users_without_role:
                    user.role = 'user'  # 设置为普通用户
                db.session.commit()
                print("✓ 已更新现有用户的默认权限")
            else:
                print("✓ 所有用户都已设置权限")
            
            # 为新用户设置默认权限
            from src.config import Config
            print(f"✓ 新用户默认权限：{Config.DEFAULT_USER_ROLE}")
            
            print("\n✅ 迁移完成！")
            return True
        
        except Exception as e:
            print(f"\n❌ 迁移失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("数据库迁移：添加用户权限字段")
    print("=" * 60)
    migrate_add_role()

