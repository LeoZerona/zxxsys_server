"""Pytest 配置和 fixtures"""
import pytest
import os
import tempfile
from app import app, db
from models import User, EmailVerification
from email_service import init_mail

@pytest.fixture
def client():
    """创建测试客户端"""
    # 创建临时数据库
    db_fd, db_path = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['MAIL_USERNAME'] = ''  # 测试模式，不发送真实邮件
    app.config['MAIL_PASSWORD'] = ''
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)

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

