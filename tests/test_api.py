"""API 接口测试"""
import pytest
import json
from app import app, db
from models import User, EmailVerification

class TestHealthCheck:
    """测试健康检查接口"""
    
    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'

class TestRegisterAPI:
    """测试注册接口"""
    
    def test_register_success(self, client, sample_user):
        """测试成功注册（需要验证码）"""
        # 先发送验证码
        send_response = client.post(
            '/api/send-verification-code',
            data=json.dumps({'email': sample_user['email']}),
            content_type='application/json'
        )
        send_data = json.loads(send_response.data)
        assert send_data['success'] == True
        
        # 获取验证码
        verification_code = None
        if 'code' in send_data:
            verification_code = send_data['code']
        else:
            # 从数据库获取
            with app.app_context():
                from models import EmailVerification
                verification = EmailVerification.query.filter_by(
                    email=sample_user['email']
                ).first()
                if verification:
                    verification_code = verification.code
        
        # 注册（带验证码）
        response = client.post(
            '/api/register',
            data=json.dumps({
                'email': sample_user['email'],
                'password': sample_user['password'],
                'verification_code': verification_code
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] == True
        assert '注册成功' in data['message']
        assert 'data' in data
        assert data['data']['email'] == sample_user['email']
        assert data['data']['role'] == 'user'  # 默认权限
    
    def test_register_without_verification_code(self, client):
        """测试注册时缺少验证码"""
        response = client.post(
            '/api/register',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'password123'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert '验证码' in data['message']
    
    def test_register_with_invalid_code(self, client):
        """测试注册时使用无效验证码"""
        response = client.post(
            '/api/register',
            data=json.dumps({
                'email': 'test@example.com',
                'password': 'password123',
                'verification_code': '000000'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert '验证码' in data['message']
    
    def test_register_duplicate_email(self, client, sample_user_in_db):
        """测试重复邮箱注册"""
        # 先发送验证码
        send_response = client.post(
            '/api/send-verification-code',
            data=json.dumps({'email': sample_user_in_db.email}),
            content_type='application/json'
        )
        send_data = json.loads(send_response.data)
        code = send_data.get('code', '123456')
        
        response = client.post(
            '/api/register',
            data=json.dumps({
                'email': sample_user_in_db.email,
                'password': 'newpassword123',
                'verification_code': code
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 409
        data = json.loads(response.data)
        assert data['success'] == False
        assert '已被注册' in data['message']
    
    def test_register_invalid_email(self, client):
        """测试无效邮箱格式"""
        response = client.post(
            '/api/register',
            data=json.dumps({
                'email': 'invalid-email',
                'password': 'password123',
                'verification_code': '123456'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert '格式' in data['message']
    
    def test_register_short_password(self, client):
        """测试密码太短"""
        response = client.post(
            '/api/register',
            data=json.dumps({
                'email': 'short@example.com',
                'password': '12345',  # 少于6位
                'verification_code': '123456'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert '长度' in data['message']
    
    def test_register_empty_data(self, client):
        """测试空数据"""
        response = client.post(
            '/api/register',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400

class TestEmailVerificationAPI:
    """测试邮箱验证码接口"""
    
    def test_send_verification_code(self, client):
        """测试发送验证码"""
        response = client.post(
            '/api/send-verification-code',
            data=json.dumps({
                'email': 'code@example.com'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert '已发送' in data['message']
        
        # 测试模式下应该返回验证码（用于测试）
        if 'code' in data:
            assert len(data['code']) == 6
    
    def test_send_code_invalid_email(self, client):
        """测试无效邮箱格式"""
        response = client.post(
            '/api/send-verification-code',
            data=json.dumps({
                'email': 'invalid-email'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
    
    def test_verify_code_success(self, client):
        """测试验证码验证成功"""
        from datetime import datetime, timedelta
        
        # 先发送验证码
        send_response = client.post(
            '/api/send-verification-code',
            data=json.dumps({
                'email': 'verify@example.com'
            }),
            content_type='application/json'
        )
        
        send_data = json.loads(send_response.data)
        assert send_data['success'] == True
        
        # 获取验证码（测试模式）
        if 'code' in send_data:
            code = send_data['code']
        else:
            # 如果测试模式没有返回，从数据库获取
            with app.app_context():
                verification = EmailVerification.query.filter_by(
                    email='verify@example.com'
                ).first()
                code = verification.code
        
        # 验证验证码
        verify_response = client.post(
            '/api/verify-code',
            data=json.dumps({
                'email': 'verify@example.com',
                'code': code
            }),
            content_type='application/json'
        )
        
        assert verify_response.status_code == 200
        verify_data = json.loads(verify_response.data)
        assert verify_data['success'] == True
    
    def test_verify_code_invalid(self, client):
        """测试无效验证码"""
        response = client.post(
            '/api/verify-code',
            data=json.dumps({
                'email': 'test@example.com',
                'code': '000000'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False

class TestGetUserAPI:
    """测试获取用户接口"""
    
    def test_get_user_success(self, client, sample_user_in_db):
        """测试获取用户信息"""
        response = client.get(f'/api/users/{sample_user_in_db.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['email'] == sample_user_in_db.email
    
    def test_get_user_not_found(self, client):
        """测试获取不存在的用户"""
        response = client.get('/api/users/99999')
        
        assert response.status_code == 404

