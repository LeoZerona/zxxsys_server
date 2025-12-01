import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    # 密钥（用于会话等，生产环境应该使用环境变量）
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # 数据库配置
    # 默认使用 SQLite，生产环境建议使用 PostgreSQL 或 MySQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'app.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CORS 配置（允许的前端地址）
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')
    
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

