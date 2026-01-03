"""
登录尝试记录模型
用于记录登录失败次数，防止暴力破解
"""
from datetime import datetime
from src.models import db


class LoginAttempt(db.Model):
    """登录尝试记录"""
    __tablename__ = 'login_attempts'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)  # 用户邮箱
    ip_address = db.Column(db.String(45), nullable=True, index=True)  # IP地址
    attempt_count = db.Column(db.Integer, default=1, nullable=False)  # 失败次数
    first_attempt_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)  # 首次尝试时间
    last_attempt_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)  # 最后尝试时间
    requires_captcha = db.Column(db.Boolean, default=False, nullable=False)  # 是否需要验证码
    captcha_verified = db.Column(db.Boolean, default=False, nullable=False)  # 验证码是否已验证
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'email': self.email,
            'ip_address': self.ip_address,
            'attempt_count': self.attempt_count,
            'first_attempt_at': self.first_attempt_at.isoformat() if self.first_attempt_at else None,
            'last_attempt_at': self.last_attempt_at.isoformat() if self.last_attempt_at else None,
            'requires_captcha': self.requires_captcha,
            'captcha_verified': self.captcha_verified
        }
    
    def reset(self):
        """重置尝试记录"""
        self.attempt_count = 0
        self.requires_captcha = False
        self.captcha_verified = False
        self.first_attempt_at = datetime.utcnow()
        self.last_attempt_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<LoginAttempt {self.email} - {self.attempt_count} attempts>'

