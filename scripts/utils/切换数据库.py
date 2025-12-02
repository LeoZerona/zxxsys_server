"""
快速切换数据库类型的辅助脚本
"""
import os

def show_current_config():
    """显示当前数据库配置"""
    from src.config import Config
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    db_type = 'MySQL' if 'mysql' in db_uri.lower() else 'SQLite' if 'sqlite' in db_uri.lower() else 'Unknown'
    
    print("="*80)
    print("📊 当前数据库配置")
    print("="*80)
    print(f"数据库类型: {db_type}")
    print(f"数据库 URI: {db_uri}")
    print("="*80)
    print()

def switch_to_mysql():
    """切换到 MySQL"""
    print("切换到 MySQL 数据库...")
    print()
    print("请创建或修改 .env 文件，添加以下内容：")
    print()
    print("DB_TYPE=mysql")
    print("MYSQL_USER=root")
    print("MYSQL_PASSWORD=123456")
    print("MYSQL_HOST=localhost")
    print("MYSQL_PORT=3306")
    print("MYSQL_DATABASE=test")
    print()

def switch_to_sqlite():
    """切换到 SQLite"""
    print("切换到 SQLite 数据库...")
    print()
    print("请创建或修改 .env 文件，添加以下内容：")
    print()
    print("DB_TYPE=sqlite")
    print("SQLITE_DB_PATH=app.db")
    print()

if __name__ == "__main__":
    print("="*80)
    print("🔧 数据库配置切换工具")
    print("="*80)
    print()
    
    # 显示当前配置
    try:
        show_current_config()
    except Exception as e:
        print(f"无法读取当前配置: {e}")
        print()
    
    print("请选择要使用的数据库类型：")
    print("1. MySQL (默认)")
    print("2. SQLite")
    print()
    
    choice = input("请输入选择 (1 或 2，直接回车使用 MySQL): ").strip()
    
    if choice == '2':
        switch_to_sqlite()
    else:
        switch_to_mysql()
    
    print("="*80)
    print("💡 提示:")
    print("   1. 创建或修改 .env 文件后，重启 Flask 服务")
    print("   2. 确保 MySQL 服务已启动（如果使用 MySQL）")
    print("   3. 确保数据库和表已创建")
    print("="*80)

