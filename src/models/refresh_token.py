"""
刷新 Token 数据模型
用于存储 Refresh Token（可选，如果需要在服务端管理）
"""
from datetime import datetime
from src.models import db


class RefreshToken(db.Model):
    """刷新 Token 模型（可选，用于服务端 Token 管理）"""
    __tablename__ = 'refresh_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    token_hash = db.Column(db.String(255), nullable=False, unique=True, index=True)  # Token 的哈希值
    is_revoked = db.Column(db.Boolean, default=False, nullable=False)  # 是否已撤销
    expires_at = db.Column(db.DateTime, nullable=False)  # 过期时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, default=datetime.utcnow)  # 最后使用时间
    user_agent = db.Column(db.String(255))  # 用户代理信息
    ip_address = db.Column(db.String(45))  # IP 地址
    
    # 关联关系
    user = db.relationship('User', backref='refresh_tokens')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'is_revoked': self.is_revoked,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None
        }
    
    def is_expired(self):
        """检查是否过期"""
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f'<RefreshToken {self.user_id}: {self.token_hash[:8]}...>'

