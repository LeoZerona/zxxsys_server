"""数据库初始化脚本"""
from src.app import app
from src.models import db

with app.app_context():
    # 创建所有表
    db.create_all()
    print("数据库表创建成功！")

