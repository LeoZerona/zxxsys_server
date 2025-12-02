from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import re

db = SQLAlchemy()

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False, index=True)  # 用户权限：super_admin(超级管理员), admin(管理员), user(普通用户)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    @staticmethod
    def is_md5_hash(value):
        """检查字符串是否是 MD5 哈希值（32位十六进制）"""
        if not value:
            return False
        md5_pattern = re.compile(r'^[a-fA-F0-9]{32}$')
        return bool(md5_pattern.match(value))
    
    @staticmethod
    def md5_hash(value):
        """计算字符串的 MD5 哈希值"""
        return hashlib.md5(value.encode('utf-8')).hexdigest()
    
    def set_password(self, password):
        """
        设置密码（加密）
        如果前端传的是 MD5 值，会在 MD5 基础上再次使用安全的哈希算法（scrypt/pbkdf2）
        """
        # 如果已经是 MD5 哈希值，直接在 MD5 基础上再次加密
        if self.is_md5_hash(password):
            # 前端已经 MD5 加密，后端再进行一次安全的哈希
            self.password_hash = generate_password_hash(password, method='scrypt')
        else:
            # 如果是明文密码，先 MD5 再加密（与前端保持一致）
            md5_password = self.md5_hash(password)
            self.password_hash = generate_password_hash(md5_password, method='scrypt')
    
    def check_password(self, password):
        """
        验证密码
        支持两种方式：
        1. 前端传 MD5 值：直接验证
        2. 前端传明文：先 MD5 再验证
        """
        # 检查存储的密码哈希格式
        if not self.password_hash:
            return False
        
        # 如果输入是 MD5 值（32位十六进制），直接验证
        if self.is_md5_hash(password):
            return check_password_hash(self.password_hash, password)
        else:
            # 如果输入是明文，先转换为 MD5 再验证
            md5_password = self.md5_hash(password)
            return check_password_hash(self.password_hash, md5_password)
    
    def to_dict(self):
        """转换为字典（用于 JSON 响应）"""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active
        }
    
    def has_permission(self, required_role):
        """检查用户是否有指定权限"""
        role_hierarchy = {
            'user': 1,
            'admin': 2,
            'super_admin': 3
        }
        user_level = role_hierarchy.get(self.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        return user_level >= required_level
    
    def is_super_admin(self):
        """检查是否为超级管理员"""
        return self.role == 'super_admin'
    
    def is_admin(self):
        """检查是否为管理员（包括超级管理员）"""
        return self.role in ['admin', 'super_admin']
    
    def __repr__(self):
        return f'<User {self.email}>'


class EmailVerification(db.Model):
    """邮箱验证码模型"""
    __tablename__ = 'email_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False, index=True)
    code = db.Column(db.String(10), nullable=False)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'email': self.email,
            'is_used': self.is_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
    
    def __repr__(self):
        return f'<EmailVerification {self.email}: {self.code}>'

