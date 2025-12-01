"""邮箱服务测试"""
import pytest
from datetime import datetime, timedelta
from app import app, db
from models import EmailVerification
from email_service import generate_verification_code, send_verification_code, verify_code

class TestEmailVerificationCode:
    """测试邮箱验证码功能"""
    
    def test_generate_verification_code(self):
        """测试生成验证码"""
        code = generate_verification_code(6)
        assert len(code) == 6
        assert code.isdigit()
        
        code_long = generate_verification_code(8)
        assert len(code_long) == 8
    
    def test_send_verification_code(self, client):
        """测试发送验证码"""
        with app.app_context():
            result = send_verification_code('test@example.com')
            
            assert result['success'] == True
            assert 'message' in result
            
            # 检查数据库中是否保存了验证码
            verification = EmailVerification.query.filter_by(email='test@example.com').first()
            assert verification is not None
            assert len(verification.code) == 6
            assert verification.is_used == False
            assert verification.expires_at > datetime.utcnow()
    
    def test_send_verification_code_updates_existing(self, client):
        """测试发送验证码会更新已存在的验证码"""
        from datetime import datetime, timedelta
        
        with app.app_context():
            # 创建旧的验证码
            old_expires = datetime.utcnow() + timedelta(minutes=5)
            old_verification = EmailVerification(
                email='update@example.com',
                code='111111',
                expires_at=old_expires
            )
            db.session.add(old_verification)
            db.session.commit()
            
            old_id = old_verification.id
            
            # 发送新验证码
            result = send_verification_code('update@example.com')
            
            assert result['success'] == True
            
            # 检查是否更新了验证码
            verification = EmailVerification.query.filter_by(email='update@example.com').first()
            assert verification.id == old_id  # 同一个记录
            assert verification.code != '111111'  # 代码已更新
            assert verification.is_used == False  # 重置为未使用
    
    def test_verify_code_success(self, client):
        """测试验证码验证成功"""
        from datetime import datetime, timedelta
        
        with app.app_context():
            # 创建验证码
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            verification = EmailVerification(
                email='verify@example.com',
                code='123456',
                expires_at=expires_at,
                is_used=False
            )
            db.session.add(verification)
            db.session.commit()
            
            # 验证验证码
            result = verify_code('verify@example.com', '123456')
            
            assert result['success'] == True
            assert '验证成功' in result['message']
            
            # 检查验证码是否被标记为已使用
            verification = EmailVerification.query.filter_by(email='verify@example.com').first()
            assert verification.is_used == True
    
    def test_verify_code_invalid(self, client):
        """测试无效验证码"""
        with app.app_context():
            result = verify_code('invalid@example.com', '999999')
            
            assert result['success'] == False
            assert '无效' in result['message']
    
    def test_verify_code_expired(self, client):
        """测试过期验证码"""
        from datetime import datetime, timedelta
        
        with app.app_context():
            # 创建已过期的验证码
            expires_at = datetime.utcnow() - timedelta(minutes=1)
            verification = EmailVerification(
                email='expired@example.com',
                code='123456',
                expires_at=expires_at,
                is_used=False
            )
            db.session.add(verification)
            db.session.commit()
            
            result = verify_code('expired@example.com', '123456')
            
            assert result['success'] == False
            assert '过期' in result['message']
    
    def test_verify_code_already_used(self, client):
        """测试已使用的验证码"""
        from datetime import datetime, timedelta
        
        with app.app_context():
            # 创建已使用的验证码
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            verification = EmailVerification(
                email='used@example.com',
                code='123456',
                expires_at=expires_at,
                is_used=True
            )
            db.session.add(verification)
            db.session.commit()
            
            result = verify_code('used@example.com', '123456')
            
            assert result['success'] == False
            assert '无效' in result['message']

