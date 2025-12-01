"""数据库初始化脚本"""
from app import app
from models import db

with app.app_context():
    # 创建所有表
    db.create_all()
    print("数据库表创建成功！")

