"""
快速测试用户注册功能
测试注册接口是否正常工作，验证数据是否成功写入数据库
"""
import sys
import os
from pathlib import Path
import io

# Windows 控制台编码修复
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except AttributeError:
        pass

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import requests
import json
import random
import string
from datetime import datetime

def generate_test_email():
    """生成测试邮箱"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_str}@example.com"

def create_test_verification_code(email, code="123456", expire_minutes=10):
    """
    直接创建测试验证码到数据库（不发送邮件）
    """
    from src.app import app
    from src.models import db, EmailVerification
    from datetime import timedelta
    
    with app.app_context():
        # 检查是否已存在该邮箱的验证码
        existing = EmailVerification.query.filter_by(
            email=email,
            is_used=False
        ).order_by(EmailVerification.created_at.desc()).first()
        
        if existing:
            # 更新现有验证码
            existing.code = code
            existing.expires_at = datetime.utcnow() + timedelta(minutes=expire_minutes)
            existing.is_used = False
            existing.created_at = datetime.utcnow()
            verification = existing
        else:
            # 创建新验证码
            verification = EmailVerification(
                email=email,
                code=code,
                expires_at=datetime.utcnow() + timedelta(minutes=expire_minutes)
            )
            db.session.add(verification)
        
        db.session.commit()
        return verification

def test_register():
    """测试用户注册"""
    print("="*80)
    print("🧪 测试用户注册功能")
    print("="*80)
    print()
    
    # 生成测试数据
    test_email = generate_test_email()
    test_password = "test123456"  # 测试密码（可以是明文或MD5）
    test_code = "123456"  # 测试验证码
    
    print(f"📧 测试邮箱: {test_email}")
    print(f"🔐 测试密码: {test_password}")
    print(f"🔑 验证码: {test_code}")
    print()
    
    # 直接创建测试验证码（不发送邮件）
    print("🔧 创建测试验证码到数据库...")
    create_test_verification_code(test_email, test_code)
    print("✅ 测试验证码已创建")
    print()
    
    # 准备请求数据
    url = "http://localhost:5000/api/register"
    data = {
        "email": test_email,
        "password": test_password,
        "verification_code": test_code
    }
    
    print("📤 发送注册请求...")
    print(f"   URL: {url}")
    print(f"   数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    print()
    
    try:
        response = requests.post(url, json=data, timeout=10)
        result = response.json()
        
        print(f"📥 响应状态码: {response.status_code}")
        print(f"📥 响应内容:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()
        
        if response.status_code == 201:
            print("✅ 注册成功！")
            print()
            
            # 验证数据库中的数据
            print("🔍 验证数据库中的数据...")
            verify_database(test_email)
            return True
        else:
            print(f"❌ 注册失败: {result.get('error', '未知错误')}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败: 请确保 Flask 应用正在运行 (python app.py)")
        print("   应用应该在 http://localhost:5000 运行")
        return False
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_database(email):
    """验证数据库中的数据"""
    try:
        from src.app import app
        from src.models import db, User
        
        with app.app_context():
            user = User.query.filter_by(email=email).first()
            
            if user:
                print()
                print("="*80)
                print("✅ 数据库验证成功！")
                print("="*80)
                print(f"用户 ID: {user.id}")
                print(f"邮箱: {user.email}")
                print(f"角色: {user.role}")
                print(f"创建时间: {user.created_at}")
                print(f"是否激活: {'是' if user.is_active else '否'}")
                print(f"密码哈希: {user.password_hash[:50]}...")
                print("="*80)
                
                # 验证密码
                if user.check_password("test123456"):
                    print("✅ 密码验证通过")
                else:
                    print("⚠️  密码验证失败")
                
                return True
            else:
                print("❌ 数据库中未找到该用户")
                return False
                
    except Exception as e:
        print(f"❌ 数据库验证失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print()
    print("🚀 开始测试用户注册功能")
    print()
    print("📌 提示:")
    print("   1. 请确保 Flask 应用正在运行 (python app.py)")
    print("   2. 应用应该在 http://localhost:5000 运行")
    print("   3. 使用万能验证码 '123456'（开发环境默认）")
    print()
    print("-"*80)
    print()
    
    success = test_register()
    
    print()
    print("="*80)
    if success:
        print("✅ 测试完成！")
    else:
        print("❌ 测试失败！")
    print("="*80)
    print()
    
    sys.exit(0 if success else 1)

