"""
JWT Token 工具模块
用于生成和验证 JWT Token
"""
import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from src.models import User
from src.config import Config


class JWTUtils:
    """JWT 工具类"""
    
    # 从配置或环境变量获取密钥
    SECRET_KEY = os.environ.get('JWT_SECRET_KEY', Config.SECRET_KEY)
    
    # Token 过期时间（秒）
    ACCESS_TOKEN_EXPIRE = int(os.environ.get('ACCESS_TOKEN_EXPIRE', 3600))  # 1小时
    REFRESH_TOKEN_EXPIRE = int(os.environ.get('REFRESH_TOKEN_EXPIRE', 7 * 24 * 3600))  # 7天
    
    # 算法
    ALGORITHM = 'HS256'
    
    @classmethod
    def generate_access_token(cls, user_id: int, email: str, role: str):
        """
        生成访问令牌（Access Token）
        
        Args:
            user_id: 用户ID
            email: 用户邮箱
            role: 用户角色
        
        Returns:
            str: JWT Token 字符串
        """
        payload = {
            'user_id': user_id,
            'email': email,
            'role': role,
            'type': 'access',  # Token 类型
            'exp': datetime.utcnow() + timedelta(seconds=cls.ACCESS_TOKEN_EXPIRE),
            'iat': datetime.utcnow(),  # 签发时间
        }
        
        token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return token
    
    @classmethod
    def generate_refresh_token(cls, user_id: int):
        """
        生成刷新令牌（Refresh Token）
        
        Args:
            user_id: 用户ID
        
        Returns:
            str: JWT Token 字符串
        """
        payload = {
            'user_id': user_id,
            'type': 'refresh',  # Token 类型
            'exp': datetime.utcnow() + timedelta(seconds=cls.REFRESH_TOKEN_EXPIRE),
            'iat': datetime.utcnow(),
        }
        
        token = jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        return token
    
    @classmethod
    def verify_token(cls, token: str, token_type: str = 'access'):
        """
        验证 Token
        
        Args:
            token: JWT Token 字符串
            token_type: Token 类型 ('access' 或 'refresh')
        
        Returns:
            dict: 验证结果
                - success: 是否成功
                - payload: Token 载荷（成功时）
                - message: 错误信息（失败时）
        """
        try:
            payload = jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
            
            # 验证 Token 类型
            if payload.get('type') != token_type:
                return {
                    'success': False,
                    'message': f'Token 类型不匹配，期望 {token_type}'
                }
            
            return {
                'success': True,
                'payload': payload
            }
        
        except jwt.ExpiredSignatureError:
            return {
                'success': False,
                'message': 'Token 已过期'
            }
        except jwt.InvalidTokenError as e:
            return {
                'success': False,
                'message': f'Token 无效: {str(e)}'
            }
    
    @classmethod
    def decode_token(cls, token: str):
        """
        解码 Token（不验证签名，仅用于调试）
        
        Args:
            token: JWT Token 字符串
        
        Returns:
            dict: Token 载荷
        """
        try:
            return jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM], options={"verify_signature": False})
        except:
            return None


def get_token_from_header():
    """
    从请求头中提取 Token
    
    Returns:
        str: Token 字符串，如果没有则返回 None
    """
    # 优先从 Authorization header 获取
    auth_header = request.headers.get('Authorization', '')
    if auth_header:
        # 支持 Bearer token 格式
        parts = auth_header.split(' ')
        if len(parts) == 2 and parts[0].lower() == 'bearer':
            return parts[1]
        # 也支持直接传 token
        return auth_header
    
    # 也可以从 X-Access-Token header 获取
    return request.headers.get('X-Access-Token', None)


def login_required(f):
    """
    登录验证装饰器
    验证请求中的 Token，并将用户信息附加到 g 对象
    
    注意：如果中间件已经验证并设置了 g.current_user，则直接使用，避免重复验证
    
    Usage:
        @app.route('/api/protected')
        @login_required
        def protected_route():
            user = g.current_user
            return jsonify({'message': f'Hello {user.email}'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 如果中间件已经验证并设置了用户信息，直接使用
        if hasattr(g, 'current_user') and g.current_user:
            return f(*args, **kwargs)
        
        # 否则进行验证（如果路由不在中间件处理的范围内）
        # 提取 Token
        token = get_token_from_header()
        
        if not token:
            return jsonify({
                'success': False,
                'message': '未提供 Token，请先登录',
                'code': 'NO_TOKEN'
            }), 401
        
        # 验证 Token
        verify_result = JWTUtils.verify_token(token, token_type='access')
        
        if not verify_result['success']:
            return jsonify({
                'success': False,
                'message': verify_result['message'],
                'code': 'INVALID_TOKEN'
            }), 401
        
        payload = verify_result['payload']
        user_id = payload.get('user_id')
        
        # 查询用户
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在',
                'code': 'USER_NOT_FOUND'
            }), 401
        
        # 检查用户状态（是否被封禁）
        if not user.is_active:
            return jsonify({
                'success': False,
                'message': '账户已被禁用，请联系管理员',
                'code': 'USER_BANNED'
            }), 403
        
        # 将用户信息附加到 g 对象
        g.current_user = user
        g.token_payload = payload
        
        return f(*args, **kwargs)
    
    return decorated_function


def role_required(*required_roles):
    """
    角色权限装饰器（RBAC）
    需要用户具有指定的角色之一
    
    Args:
        *required_roles: 允许的角色列表
    
    Usage:
        @app.route('/api/admin')
        @login_required
        @role_required('admin', 'super_admin')
        def admin_route():
            return jsonify({'message': 'Admin access granted'})
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            user = g.current_user
            
            # 检查用户角色
            if user.role not in required_roles:
                return jsonify({
                    'success': False,
                    'message': f'权限不足，需要角色: {", ".join(required_roles)}',
                    'code': 'INSUFFICIENT_PERMISSIONS',
                    'required_roles': list(required_roles),
                    'user_role': user.role
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def permission_required(permission: str):
    """
    权限点验证装饰器（RBAC 细粒度权限）
    需要用户具有指定的权限点
    
    Args:
        permission: 权限点名称（如 'user:read', 'article:write'）
    
    Usage:
        @app.route('/api/articles')
        @login_required
        @permission_required('article:read')
        def get_articles():
            return jsonify({'articles': []})
    """
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            user = g.current_user
            
            # TODO: 实现权限点检查逻辑
            # 这里可以扩展为从数据库读取用户的权限点列表
            # 目前基于角色进行权限判断
            
            # 默认权限映射（可以根据实际需求扩展）
            role_permissions = {
                'super_admin': ['*'],  # 超级管理员拥有所有权限
                'admin': ['user:read', 'user:write', 'article:read', 'article:write'],
                'user': ['article:read', 'user:read']
            }
            
            user_permissions = role_permissions.get(user.role, [])
            
            # 检查权限
            has_permission = (
                '*' in user_permissions or  # 拥有所有权限
                permission in user_permissions  # 拥有指定权限
            )
            
            if not has_permission:
                return jsonify({
                    'success': False,
                    'message': f'权限不足，需要权限: {permission}',
                    'code': 'INSUFFICIENT_PERMISSIONS',
                    'required_permission': permission
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

