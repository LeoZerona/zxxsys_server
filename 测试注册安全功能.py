"""
测试注册功能的安全检查
验证所有安全功能是否正常工作
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
import time

BASE_URL = "http://localhost:5000"

def print_test(name):
    """打印测试标题"""
    print("\n" + "="*80)
    print(f"测试: {name}")
    print("="*80)

def test_email_format_validation():
    """测试邮箱格式验证"""
    print_test("邮箱格式验证")
    
    invalid_emails = [
        "invalid-email",
        "test@",
        "@example.com",
        "test@example",
        "",
        "test@.com",
        "@",
        "test..test@example.com"
    ]
    
    for email in invalid_emails:
        response = requests.post(f"{BASE_URL}/api/register", json={
            "email": email,
            "password": "test123456",
            "verification_code": "123456"
        })
        result = response.json()
        print(f"邮箱: {email:30} -> {result.get('message', '未知错误')}")

def create_test_verification_code(email, code="123456", expire_minutes=10):
    """
    直接创建测试验证码到数据库（不发送邮件）
    """
    from src.app import app
    from src.models import db, EmailVerification
    from datetime import timedelta, datetime
    
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

def test_verification_code_email_match():
    """测试验证码和邮箱匹配验证"""
    print_test("验证码和邮箱匹配验证")
    
    # 为邮箱A创建测试验证码（不发送邮件）
    email_a = "test_a@example.com"
    email_b = "test_b@example.com"
    code_a = "111111"
    
    print(f"1. 为邮箱 {email_a} 创建测试验证码...")
    create_test_verification_code(email_a, code_a)
    print(f"   验证码: {code_a}")
    
    # 尝试使用邮箱A的验证码注册邮箱B
    print(f"\n2. 尝试使用 {email_a} 的验证码注册 {email_b}...")
    response = requests.post(f"{BASE_URL}/api/register", json={
        "email": email_b,
        "password": "test123456",
        "verification_code": code_a
    })
    result = response.json()
    print(f"   结果: {result.get('message', '未知错误')}")
    if not result.get('success'):
        print("   ✅ 安全防护生效：无法使用其他邮箱的验证码注册")
    else:
        print("   ❌ 安全漏洞：可以使用其他邮箱的验证码注册")

def test_latest_verification_code():
    """测试使用最新验证码"""
    print_test("验证码最新性检查")
    
    email = "test_latest@example.com"
    code1 = "111111"
    code2 = "222222"
    
    # 创建第一个验证码（不发送邮件）
    print(f"1. 为 {email} 创建第一个验证码...")
    create_test_verification_code(email, code1)
    print(f"   第一个验证码: {code1}")
    
    # 等待1秒后创建第二个验证码
    time.sleep(1)
    print(f"\n2. 创建第二个验证码（新的验证码）...")
    create_test_verification_code(email, code2)
    print(f"   第二个验证码: {code2}")
    
    # 尝试使用第一个验证码注册
    print(f"\n3. 尝试使用第一个验证码 {code1} 注册...")
    response = requests.post(f"{BASE_URL}/api/register", json={
        "email": email,
        "password": "test123456",
        "verification_code": code1
    })
    result = response.json()
    print(f"   结果: {result.get('message', '未知错误')}")
    if not result.get('success'):
        if '最新' in result.get('message', ''):
            print("   ✅ 安全防护生效：必须使用最新发送的验证码")
        else:
            print(f"   ⚠️  验证失败，但原因: {result.get('message')}")
    else:
        print("   ❌ 安全漏洞：可以使用旧的验证码注册")
    
    # 使用第二个验证码注册（应该成功）
    print(f"\n4. 使用第二个验证码 {code2} 注册...")
    response = requests.post(f"{BASE_URL}/api/register", json={
        "email": email,
        "password": "test123456",
        "verification_code": code2
    })
    result = response.json()
    if result.get('success'):
        print("   ✅ 使用最新验证码注册成功")
    else:
        print(f"   ❌ 注册失败: {result.get('message')}")

def main():
    """主测试函数"""
    print("="*80)
    print("注册功能安全测试")
    print("="*80)
    print(f"后端地址: {BASE_URL}")
    print()
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正在运行")
        else:
            print("⚠️  后端服务响应异常")
            return
    except:
        print("❌ 无法连接到后端服务!")
        print("💡 请先启动后端服务: python app.py")
        return
    
    # 执行测试
    test_email_format_validation()
    test_verification_code_email_match()
    test_latest_verification_code()
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)

if __name__ == '__main__':
    main()

