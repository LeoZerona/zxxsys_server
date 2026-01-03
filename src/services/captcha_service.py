"""
验证码服务
用于生成和验证图形验证码（防止暴力破解）
"""
import random
import string
import hashlib
import time
from datetime import datetime, timedelta
from flask import session
from src.models import db


class CaptchaService:
    """验证码服务类"""
    
    # 验证码配置
    CAPTCHA_LENGTH = 4  # 验证码长度（4位数字）
    CAPTCHA_EXPIRE_MINUTES = 5  # 验证码有效期（分钟）
    
    @staticmethod
    def generate_captcha():
        """
        生成验证码
        返回验证码字符串和会话键
        """
        # 生成4位数字验证码
        captcha_code = ''.join(random.choices(string.digits, k=CaptchaService.CAPTCHA_LENGTH))
        
        # 生成会话键（用于标识验证码）
        session_key = hashlib.md5(
            f"{captcha_code}{time.time()}{random.random()}".encode()
        ).hexdigest()[:16]
        
        # 将验证码存储到session（后端存储）
        # 注意：这里使用内存存储，生产环境建议使用Redis
        # 将datetime转换为ISO格式字符串，避免序列化问题
        expires_at = datetime.utcnow() + timedelta(minutes=CaptchaService.CAPTCHA_EXPIRE_MINUTES)
        session[f'captcha_{session_key}'] = {
            'code': captcha_code.lower(),  # 不区分大小写
            'expires_at': expires_at.isoformat(),  # 转换为ISO格式字符串
            'created_at': datetime.utcnow().isoformat()
        }
        
        print(f"   🔐 生成验证码: {captcha_code} (会话键: {session_key})")
        
        return {
            'captcha_code': captcha_code,
            'session_key': session_key,
            'expires_in': CaptchaService.CAPTCHA_EXPIRE_MINUTES * 60  # 秒
        }
    
    @staticmethod
    def verify_captcha(session_key, user_input):
        """
        验证验证码
        :param session_key: 会话键（从生成验证码接口获取）
        :param user_input: 用户输入的验证码
        :return: 验证结果字典
        """
        if not session_key or not user_input:
            return {
                'success': False,
                'message': '验证码参数不能为空'
            }
        
        # 从session获取验证码
        captcha_data = session.get(f'captcha_{session_key}')
        
        if not captcha_data:
            return {
                'success': False,
                'message': '验证码不存在或已过期，请重新获取'
            }
        
        # 检查是否过期
        expires_at = captcha_data.get('expires_at')
        if isinstance(expires_at, str):
            # 解析ISO格式字符串（可能带Z或不带时区信息）
            try:
                if expires_at.endswith('Z'):
                    expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                elif '+' in expires_at or expires_at.count('-') > 2:
                    # 带时区信息
                    expires_at = datetime.fromisoformat(expires_at)
                else:
                    # 不带时区信息，假设是UTC
                    expires_at = datetime.fromisoformat(expires_at + '+00:00')
            except (ValueError, AttributeError):
                return {
                    'success': False,
                    'message': '验证码数据格式错误'
                }
        elif isinstance(expires_at, datetime):
            pass
        else:
            return {
                'success': False,
                'message': '验证码数据格式错误'
            }
        
        # 确保都是UTC时间（如果expires_at有时区信息，需要转换）
        if expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)  # 转换为naive datetime（假设是UTC）
        
        if datetime.utcnow() > expires_at:
            # 清除过期的验证码
            session.pop(f'captcha_{session_key}', None)
            return {
                'success': False,
                'message': '验证码已过期，请重新获取'
            }
        
        # 验证码不区分大小写
        stored_code = str(captcha_data.get('code', '')).lower().strip()
        user_code = str(user_input).lower().strip()
        
        if stored_code != user_code:
            return {
                'success': False,
                'message': '验证码错误'
            }
        
        # 验证成功后，清除验证码（一次性使用）
        session.pop(f'captcha_{session_key}', None)
        
        print(f"   ✅ 验证码验证成功: {user_code}")
        
        return {
            'success': True,
            'message': '验证码验证成功'
        }
    
    @staticmethod
    def clear_captcha(session_key):
        """清除验证码"""
        if session_key:
            session.pop(f'captcha_{session_key}', None)

