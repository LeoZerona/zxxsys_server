"""Pytest 配置和 fixtures"""
import pytest
import os
from app import app, db
from models import User, EmailVerification
from email_service import init_mail

@pytest.fixture
def client():
    """创建测试客户端（使用 MySQL test 数据库）"""
    # 使用 MySQL test 数据库
    mysql_user = os.environ.get('MYSQL_USER', 'root')
    mysql_password = os.environ.get('MYSQL_PASSWORD', '123456')
    mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
    mysql_port = os.environ.get('MYSQL_PORT', '3306')
    
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/test?charset=utf8mb4'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['MAIL_USERNAME'] = ''  # 测试模式，不发送真实邮件
    app.config['MAIL_PASSWORD'] = ''
    
    with app.test_client() as client:
        with app.app_context():
            # 确保表存在
            db.create_all()
            yield client
            # 测试完成后不删除数据，保留在 MySQL test 数据库中

@pytest.fixture
def sample_user():
    """示例用户数据"""
    return {
        'email': 'test@example.com',
        'password': 'test123456'
    }

@pytest.fixture
def sample_user_in_db(client, sample_user):
    """在数据库中创建示例用户"""
    with app.app_context():
        user = User(email=sample_user['email'])
        user.set_password(sample_user['password'])
        db.session.add(user)
        db.session.commit()
        return user

