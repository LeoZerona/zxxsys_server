"""测试验证码发送频率限制"""
import pytest
import time
from src.app import app, db
from src.models import EmailVerification
from src.services.email_service import send_verification_code

class TestVerificationCodeFrequencyLimit:
    """测试验证码发送频率限制"""
    
    def test_send_code_twice_quickly(self, client):
        """测试1分钟内连续发送两次验证码"""
        with app.app_context():
            email = 'frequency@example.com'
            
            # 第一次发送
            result1 = send_verification_code(email)
            assert result1['success'] == True
            
            # 立即第二次发送（应该被限制）
            result2 = send_verification_code(email)
            assert result2['success'] == False
            assert '频繁' in result2['message'] or '等待' in result2['message']
            assert 'cooldown_seconds' in result2
    
    def test_send_code_after_cooldown(self, client):
        """测试冷却时间后可以再次发送"""
        from datetime import datetime, timedelta
        
        with app.app_context():
            email = 'cooldown@example.com'
            
            # 第一次发送
            result1 = send_verification_code(email)
            assert result1['success'] == True
            
            # 模拟等待1分钟后（手动修改created_at）
            verification = EmailVerification.query.filter_by(email=email).first()
            verification.created_at = datetime.utcnow() - timedelta(minutes=2)
            db.session.commit()
            
            # 第二次发送（应该成功）
            result2 = send_verification_code(email)
            assert result2['success'] == True
    
    def test_frequency_limit_api(self, client):
        """测试API接口的频率限制"""
        import json
        
        email = 'api_frequency@example.com'
        
        # 第一次发送
        response1 = client.post(
            '/api/send-verification-code',
            data=json.dumps({'email': email}),
            content_type='application/json'
        )
        
        assert response1.status_code == 200
        data1 = json.loads(response1.data)
        assert data1['success'] == True
        
        # 立即第二次发送
        response2 = client.post(
            '/api/send-verification-code',
            data=json.dumps({'email': email}),
            content_type='application/json'
        )
        
        assert response2.status_code == 429  # Too Many Requests
        data2 = json.loads(response2.data)
        assert data2['success'] == False
        assert '频繁' in data2['message'] or '等待' in data2['message']
        assert 'cooldown_seconds' in data2

