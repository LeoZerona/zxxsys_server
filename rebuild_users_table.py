"""重建 users 表脚本（仅删除并重建 users 表，不影响其他表）"""
from app import app, db
from sqlalchemy import text

def rebuild_users_table():
    """删除并重建 users 表"""
    with app.app_context():
        try:
            # 检测数据库类型
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            
            print("=" * 60)
            print("重建 users 表")
            print("=" * 60)
            print(f"数据库: {db_url}")
            print()
            
            # 删除现有的 users 表
            print("正在删除现有的 users 表...")
            try:
                db.session.execute(text("DROP TABLE IF EXISTS users;"))
                db.session.commit()
                print("✅ users 表已删除")
            except Exception as e:
                print(f"⚠️  删除表时出错（可能表不存在）: {str(e)}")
                db.session.rollback()
            
            print()
            print("正在创建新的 users 表...")
            
            # 根据数据库类型执行相应的 SQL
            if 'sqlite' in db_url.lower():
                # SQLite
                db.session.execute(text("""
                    CREATE TABLE users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email VARCHAR(120) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        role VARCHAR(20) DEFAULT 'user' NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    );
                """))
                
                # 创建索引
                db.session.execute(text("CREATE INDEX idx_users_email ON users(email);"))
                db.session.execute(text("CREATE INDEX idx_users_role ON users(role);"))
                
            elif 'mysql' in db_url.lower():
                # MySQL
                db.session.execute(text("""
                    CREATE TABLE users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        email VARCHAR(120) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        role VARCHAR(20) NOT NULL DEFAULT 'user',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        is_active TINYINT(1) DEFAULT 1,
                        INDEX idx_users_email (email),
                        INDEX idx_users_role (role)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
                """))
                
            elif 'postgresql' in db_url.lower() or 'postgres' in db_url.lower():
                # PostgreSQL
                db.session.execute(text("""
                    CREATE TABLE users (
                        id SERIAL PRIMARY KEY,
                        email VARCHAR(120) NOT NULL UNIQUE,
                        password_hash VARCHAR(255) NOT NULL,
                        role VARCHAR(20) NOT NULL DEFAULT 'user',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE
                    );
                """))
                
                # 创建索引
                db.session.execute(text("CREATE INDEX idx_users_email ON users(email);"))
                db.session.execute(text("CREATE INDEX idx_users_role ON users(role);"))
                
                # 创建更新时间触发器函数（如果不存在）
                db.session.execute(text("""
                    CREATE OR REPLACE FUNCTION update_updated_at_column()
                    RETURNS TRIGGER AS $$
                    BEGIN
                        NEW.updated_at = CURRENT_TIMESTAMP;
                        RETURN NEW;
                    END;
                    $$ language 'plpgsql';
                """))
                
                # 创建触发器（自动更新 updated_at）
                db.session.execute(text("""
                    DROP TRIGGER IF EXISTS update_users_updated_at ON users;
                    CREATE TRIGGER update_users_updated_at 
                        BEFORE UPDATE ON users 
                        FOR EACH ROW 
                        EXECUTE FUNCTION update_updated_at_column();
                """))
            else:
                print("❌ 不支持的数据库类型")
                return False
            
            db.session.commit()
            print("✅ users 表创建成功")
            print()
            
            # 验证表结构
            print("验证表结构...")
            result = db.session.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='users';")).fetchone()
            if result:
                print("表结构:")
                print(result[0])
            
            print()
            print("=" * 60)
            print("✅ 重建完成！")
            print("=" * 60)
            print()
            print("表结构说明:")
            print("- id: 主键，自增")
            print("- email: 邮箱地址，唯一，已建立索引")
            print("- password_hash: 密码哈希值")
            print("- role: 用户权限（'super_admin', 'admin', 'user'），默认 'user'，已建立索引")
            print("- created_at: 创建时间")
            print("- updated_at: 更新时间")
            print("- is_active: 是否激活")
            
            return True
        
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 重建失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == '__main__':
    print("\n⚠️  警告：此操作将删除并重建 users 表！")
    print("   确保 users 表是空表或数据已备份。")
    print()
    
    confirm = input("确认继续？(yes/no): ").strip().lower()
    
    if confirm == 'yes':
        rebuild_users_table()
    else:
        print("操作已取消")

