"""
统一身份验证中间件
流程：接收请求 → 中间件拦截 → 提取Token → 验证签名/有效期 → 查询用户状态 → 附加user对象到请求上下文
"""
from flask import request, jsonify, g, current_app
from functools import wraps
from src.utils.jwt_utils import JWTUtils, get_token_from_header
from src.models import User
import hashlib
import secrets


def csrf_protect(f):
    """
    CSRF 防护装饰器
    验证请求头中的 X-CSRF-Token
    
    Usage:
        @app.route('/api/sensitive')
        @csrf_protect
        @login_required
        def sensitive_route():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 对于 GET、HEAD、OPTIONS 请求，通常不需要 CSRF 保护
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return f(*args, **kwargs)
        
        # 从请求头获取 CSRF Token
        csrf_token = request.headers.get('X-CSRF-Token')
        
        if not csrf_token:
            return jsonify({
                'success': False,
                'message': '缺少 CSRF Token',
                'code': 'MISSING_CSRF_TOKEN'
            }), 403
        
        # 从用户会话或 Token 中获取预期的 CSRF Token
        # 这里简化处理：从 Token 中获取 user_id，然后验证
        # 实际应用中，CSRF Token 应该存储在会话中或与 Token 关联
        
        # 简化版本：检查 Token 是否存在（如果用户已登录）
        # 更完善的实现可以将 CSRF Token 存储在 Redis 中，与用户 ID 关联
        if hasattr(g, 'current_user'):
            # 用户已通过认证，可以进一步验证 CSRF Token
            # TODO: 实现完整的 CSRF Token 验证逻辑
            pass
        
        return f(*args, **kwargs)
    
    return decorated_function


def generate_csrf_token():
    """
    生成 CSRF Token
    
    Returns:
        str: CSRF Token 字符串
    """
    return secrets.token_urlsafe(32)


def init_auth_middleware(app):
    """
    初始化认证中间件
    在应用启动时调用，注册全局的 before_request 钩子
    
    Args:
        app: Flask 应用实例
    """
    
    @app.before_request
    def before_request():
        """
        在每个请求之前执行
        对需要认证的接口进行 Token 验证
        """
        # 公开接口列表（不需要认证）
        public_endpoints = [
            '/api/register',           # 用户注册
            '/api/login',              # 用户登录
            '/api/refresh-token',      # 刷新Token
            '/api/logout',             # 登出（允许未登录调用，但内部会检查）
            '/api/send-verification-code',  # 发送邮箱验证码
            '/api/verify-code',        # 验证邮箱验证码
            '/api/captcha',            # 获取图形验证码
            '/api/health',             # 健康检查
            '/',                       # 根路径
        ]
        
        # 静态文件不需要认证
        if request.path.startswith('/static/'):
            return None
        
        # 检查当前请求路径是否在公开列表中
        if request.path in public_endpoints:
            return None  # 不需要认证，继续处理请求
        
        # 对于其他 API 请求，检查是否需要认证
        if request.path.startswith('/api/'):
            # 提取 Token
            token = get_token_from_header()
            
            if not token:
                print(f"   ⚠️ Token 验证失败: 未提供 Token - {request.path}")
                return jsonify({
                    'success': False,
                    'message': '未提供 Token，请先登录',
                    'code': 'NO_TOKEN',
                    'detail': '请在请求头中添加 Authorization: Bearer <token> 或 X-Access-Token: <token>'
                }), 401
            
            # 验证 Token
            verify_result = JWTUtils.verify_token(token, token_type='access')
            
            if not verify_result['success']:
                error_code = 'TOKEN_EXPIRED' if '过期' in verify_result['message'] else 'INVALID_TOKEN'
                print(f"   ⚠️ Token 验证失败: {verify_result['message']} - {request.path}")
                return jsonify({
                    'success': False,
                    'message': verify_result['message'],
                    'code': error_code,
                    'detail': 'Token 无效或已过期，请重新登录'
                }), 401
            
            payload = verify_result['payload']
            user_id = payload.get('user_id')
            
            # 查询用户
            user = User.query.get(user_id)
            
            if not user:
                print(f"   ⚠️ Token 验证失败: 用户不存在 (ID: {user_id}) - {request.path}")
                return jsonify({
                    'success': False,
                    'message': '用户不存在',
                    'code': 'USER_NOT_FOUND',
                    'detail': 'Token 中的用户 ID 不存在于数据库中'
                }), 401
            
            # 检查用户状态（是否被封禁）
            if not user.is_active:
                print(f"   ⚠️ Token 验证失败: 账户已被禁用 - {user.email} - {request.path}")
                return jsonify({
                    'success': False,
                    'message': '账户已被禁用，请联系管理员',
                    'code': 'USER_BANNED',
                    'detail': '您的账户已被管理员禁用，无法访问系统'
                }), 403
            
            # 将用户信息附加到 g 对象（供后续路由使用）
            g.current_user = user
            g.token_payload = payload
            print(f"   ✅ Token 验证成功: {user.email} (角色: {user.role}) - {request.path}")
        
        return None  # 继续处理请求


def hash_token(token: str):
    """
    对 Token 进行哈希（用于存储）
    
    Args:
        token: 原始 Token 字符串
    
    Returns:
        str: 哈希后的字符串
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

