"""检查当前数据库配置"""
from src.config import Config

print("="*80)
print("📊 当前数据库配置")
print("="*80)
print(f"数据库 URI: {Config.SQLALCHEMY_DATABASE_URI}")
print()

# 解析数据库信息
db_uri = Config.SQLALCHEMY_DATABASE_URI
if db_uri.startswith('sqlite'):
    print("⚠️  当前使用的是 SQLite 数据库")
    print(f"   数据库文件: {db_uri}")
elif 'mysql' in db_uri.lower():
    print("✅ 当前使用的是 MySQL 数据库")
    # 解析连接信息（不显示密码）
    if '@' in db_uri:
        parts = db_uri.split('@')
        if len(parts) == 2:
            user_part = parts[0].split('//')[1] if '//' in parts[0] else parts[0]
            if ':' in user_part:
                user = user_part.split(':')[0]
                print(f"   用户: {user}")
            host_part = parts[1].split('/')[0] if '/' in parts[1] else parts[1]
            print(f"   主机: {host_part}")
            if '/' in parts[1]:
                db_name = parts[1].split('/')[1].split('?')[0]
                print(f"   数据库: {db_name}")
elif 'postgresql' in db_uri.lower():
    print("✅ 当前使用的是 PostgreSQL 数据库")
else:
    print(f"未知的数据库类型: {db_uri}")

print("="*80)

