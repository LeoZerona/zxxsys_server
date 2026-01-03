import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    # 密钥（用于会话等，生产环境应该使用环境变量）
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # ============================================================================
    # 数据库配置
    # ============================================================================
    # 数据库类型选择: 'sqlite' 或 'mysql' (默认: mysql)
    # 可以通过环境变量 DB_TYPE 来设置，例如: DB_TYPE=mysql 或 DB_TYPE=sqlite
    DB_TYPE = os.environ.get('DB_TYPE', 'mysql').lower()  # 默认使用 MySQL
    
    # 如果环境变量明确设置了 DATABASE_URL，则优先使用它（最高优先级）
    env_db_url = os.environ.get('DATABASE_URL', '')
    if env_db_url and not env_db_url.startswith('sqlite'):
        # 如果 DATABASE_URL 是 MySQL 或其他数据库，直接使用
        SQLALCHEMY_DATABASE_URI = env_db_url
    else:
        # 根据 DB_TYPE 选择数据库配置
        if DB_TYPE == 'mysql':
            # ============================================================
            # MySQL 数据库配置（账号: root, 密码: 123456）
            # ============================================================
            mysql_user = os.environ.get('MYSQL_USER', 'root')
            mysql_password = os.environ.get('MYSQL_PASSWORD', '123456')
            mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
            mysql_port = os.environ.get('MYSQL_PORT', '3306')
            mysql_database = os.environ.get('MYSQL_DATABASE', 'test')
            
            SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_database}?charset=utf8mb4'
        
        elif DB_TYPE == 'sqlite':
            # ============================================================
            # SQLite 数据库配置
            # ============================================================
            # SQLite 数据库文件路径（放在项目根目录）
            sqlite_db_path = os.environ.get('SQLITE_DB_PATH', 'app.db')
            # 如果路径是相对路径，放在项目根目录（src的父目录）
            if not os.path.isabs(sqlite_db_path):
                # 获取项目根目录（src的父目录）
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                sqlite_db_path = os.path.join(project_root, sqlite_db_path)
            SQLALCHEMY_DATABASE_URI = f'sqlite:///{sqlite_db_path}'
        
        else:
            raise ValueError(f"不支持的数据库类型: {DB_TYPE}，请使用 'sqlite' 或 'mysql'")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CORS 配置
    # 环境变量：开发环境(development) 或 生产环境(production)
    ENV = os.environ.get('FLASK_ENV', 'development')
    
    # CORS 允许的源地址
    # 如果设置 CORS_ORIGINS=* 则允许所有来源（仅开发环境推荐）
    # 生产环境请设置具体的域名，用逗号分隔
    cors_origins_env = os.environ.get('CORS_ORIGINS', '')
    
    if cors_origins_env == '*' or cors_origins_env.lower() == 'all':
        # 允许所有来源（开发环境）
        CORS_ORIGINS = '*'
        CORS_ALLOW_ALL_ORIGINS = True
    elif cors_origins_env:
        # 使用环境变量中指定的源
        CORS_ORIGINS = [origin.strip() for origin in cors_origins_env.split(',') if origin.strip()]
        CORS_ALLOW_ALL_ORIGINS = False
    else:
        # 默认开发环境配置
        if ENV == 'production':
            # 生产环境默认不允许所有来源
            CORS_ORIGINS = ['http://localhost:5173', 'http://localhost:3000']
            CORS_ALLOW_ALL_ORIGINS = False
        else:
            # 开发环境默认配置
            CORS_ORIGINS = [
                'http://localhost:5173',  # Vite
                'http://localhost:3000',  # Create React App
                'http://localhost:8080',  # Vue CLI
                'http://127.0.0.1:5173',
                'http://127.0.0.1:3000',
                'http://127.0.0.1:8080',
                'null',  # 允许直接访问（file:// 协议）
            ]
            CORS_ALLOW_ALL_ORIGINS = False
    
    # CORS 其他配置
    CORS_SUPPORTS_CREDENTIALS = True  # 允许携带凭证（cookies等）
    CORS_ALLOW_CREDENTIALS = True
    
    # 万能验证码配置（仅用于开发测试）
    # 设置此环境变量后，该验证码可以验证任何邮箱（绕过正常验证码）
    # 生产环境请勿使用或设置为空字符串
    UNIVERSAL_VERIFICATION_CODE = os.environ.get('UNIVERSAL_VERIFICATION_CODE', '')
    # 如果未设置，默认开发环境使用 '123456' 作为万能验证码
    if not UNIVERSAL_VERIFICATION_CODE and ENV == 'development':
        UNIVERSAL_VERIFICATION_CODE = '123456'  # 默认万能验证码（仅开发环境）
    
    # 邮箱验证配置
    EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # 密码最小长度
    MIN_PASSWORD_LENGTH = 6
    
    # 邮箱服务配置
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or ''
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or ''
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or MAIL_USERNAME
    
    # 验证码配置
    VERIFICATION_CODE_LENGTH = 6
    VERIFICATION_CODE_EXPIRE_MINUTES = 10
    VERIFICATION_CODE_COOLDOWN_MINUTES = 1  # 验证码发送冷却时间（分钟）
    
    # 用户权限配置
    USER_ROLES = {
        'super_admin': '超级管理员',
        'admin': '管理员',
        'user': '普通用户'
    }
    DEFAULT_USER_ROLE = 'user'  # 默认用户权限
    
    # 登录失败限制配置
    LOGIN_FAIL_LIMIT = int(os.environ.get('LOGIN_FAIL_LIMIT', 10))  # 登录失败次数限制（默认10次）
    LOGIN_FAIL_WINDOW_MINUTES = int(os.environ.get('LOGIN_FAIL_WINDOW_MINUTES', 10))  # 时间窗口（分钟，默认10分钟）

