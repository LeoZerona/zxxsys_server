"""数据库连接和操作测试"""
import pytest
from app import app, db
from models import User, EmailVerification

class TestDatabaseConnection:
    """测试数据库连接"""
    
    def test_database_initialization(self, client):
        """测试数据库初始化"""
        with app.app_context():
            # 检查表是否创建
            assert db.engine.table_names() is not None
            # 尝试查询表
            assert User.query.count() >= 0
            assert EmailVerification.query.count() >= 0
    
    def test_database_connection(self, client):
        """测试数据库连接是否正常"""
        with app.app_context():
            # 执行简单查询
            result = db.session.execute(db.text("SELECT 1")).scalar()
            assert result == 1

class TestUserModel:
    """测试用户模型"""
    
    def test_create_user(self, client):
        """测试创建用户"""
        with app.app_context():
            user = User(email='test@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.email == 'test@example.com'
            assert user.password_hash is not None
            assert user.check_password('password123')
            assert not user.check_password('wrongpassword')
    
    def test_user_email_unique(self, client):
        """测试邮箱唯一性约束"""
        with app.app_context():
            user1 = User(email='unique@example.com')
            user1.set_password('password123')
            db.session.add(user1)
            db.session.commit()
            
            user2 = User(email='unique@example.com')
            user2.set_password('password456')
            db.session.add(user2)
            
            with pytest.raises(Exception):
                db.session.commit()
            
            db.session.rollback()
    
    def test_user_to_dict(self, client):
        """测试用户字典转换"""
        with app.app_context():
            user = User(email='dict@example.com')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            user_dict = user.to_dict()
            assert 'id' in user_dict
            assert 'email' in user_dict
            assert 'created_at' in user_dict
            assert 'is_active' in user_dict
            assert user_dict['email'] == 'dict@example.com'
            assert 'password_hash' not in user_dict  # 不应包含密码

class TestEmailVerificationModel:
    """测试邮箱验证码模型"""
    
    def test_create_verification_code(self, client):
        """测试创建验证码"""
        from datetime import datetime, timedelta
        
        with app.app_context():
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            verification = EmailVerification(
                email='verify@example.com',
                code='123456',
                expires_at=expires_at
            )
            db.session.add(verification)
            db.session.commit()
            
            assert verification.id is not None
            assert verification.email == 'verify@example.com'
            assert verification.code == '123456'
            assert verification.is_used == False
    
    def test_verification_to_dict(self, client):
        """测试验证码字典转换"""
        from datetime import datetime, timedelta
        
        with app.app_context():
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            verification = EmailVerification(
                email='dict@example.com',
                code='654321',
                expires_at=expires_at
            )
            db.session.add(verification)
            db.session.commit()
            
            verification_dict = verification.to_dict()
            assert 'id' in verification_dict
            assert 'email' in verification_dict
            assert 'code' not in verification_dict  # 验证码不应出现在字典中
            assert 'is_used' in verification_dict
            assert 'created_at' in verification_dict
            assert 'expires_at' in verification_dict

