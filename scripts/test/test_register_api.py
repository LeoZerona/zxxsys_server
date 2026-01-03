"""
用户注册功能测试脚本
测试注册接口是否正常工作，验证数据是否成功写入 MySQL test 数据库
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
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import requests
import json
import random
import string
from datetime import datetime, timedelta
from flask import Flask
from src.models import db, User, EmailVerification

# 创建 Flask 应用实例（使用 MySQL test 数据库）
app = Flask(__name__)

# 配置 MySQL test 数据库
mysql_user = os.environ.get('MYSQL_USER', 'root')
mysql_password = os.environ.get('MYSQL_PASSWORD', '123456')
mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
mysql_port = os.environ.get('MYSQL_PORT', '3306')

app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/test?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db.init_app(app)

def generate_test_email():
    """生成测试邮箱"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_str}@example.com"

def generate_test_password():
    """生成测试密码（MD5 格式）"""
    import hashlib
    random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    return hashlib.md5(random_str.encode('utf-8')).hexdigest()

def generate_test_password_plain():
    """生成测试密码（明文）"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

def create_test_verification_code(email, code="123456", expire_minutes=10):
    """
    直接创建测试验证码到数据库（不发送邮件）
    
    Args:
        email: 邮箱地址
        code: 验证码（默认使用万能验证码）
        expire_minutes: 过期时间（分钟）
    
    Returns:
        EmailVerification: 创建的验证码对象
    """
    from datetime import timedelta
    
    # 确保在 app context 中执行
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

def test_register_with_md5_password():
    """测试使用 MD5 密码注册"""
    print("\n" + "="*80)
    print("🧪 测试 1: 使用 MD5 加密密码注册")
    print("="*80)
    print(f"📊 使用数据库: MySQL test")
    print(f"🔗 连接: {mysql_user}@{mysql_host}:{mysql_port}/test")
    
    with app.app_context():
        # 生成测试数据
        test_email = generate_test_email()
        test_password = generate_test_password()  # MD5 格式
        test_code = "123456"  # 测试验证码
        
        print(f"📧 测试邮箱: {test_email}")
        print(f"🔐 测试密码 (MD5): {test_password[:16]}...")
        print(f"🔑 验证码: {test_code}")
        
        # 检查邮箱是否已存在
        existing_user = User.query.filter_by(email=test_email).first()
        if existing_user:
            print(f"⚠️  邮箱已存在，删除旧记录...")
            db.session.delete(existing_user)
            db.session.commit()
        
        # 直接创建测试验证码（不发送邮件）
        print(f"   🔧 创建测试验证码到数据库（不发送邮件）...")
        create_test_verification_code(test_email, test_code)
        print(f"   ✅ 测试验证码已创建: {test_code}")
        
        # 准备请求数据
        url = "http://localhost:5000/api/register"
        data = {
            "email": test_email,
            "password": test_password,  # MD5 格式
            "verification_code": test_code
        }
        
        print(f"\n📤 发送注册请求...")
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            print(f"📥 响应状态码: {response.status_code}")
            print(f"📥 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if response.status_code == 201 and result.get('success'):
                print(f"\n✅ 注册请求成功!")
                
                # 验证数据是否写入数据库
                print(f"\n🔍 验证数据库中的数据...")
                saved_user = User.query.filter_by(email=test_email).first()
                
                if saved_user:
                    print(f"✅ 用户数据已成功写入数据库!")
                    print(f"   - ID: {saved_user.id}")
                    print(f"   - 邮箱: {saved_user.email}")
                    print(f"   - 角色: {saved_user.role}")
                    print(f"   - 创建时间: {saved_user.created_at}")
                    print(f"   - 是否激活: {saved_user.is_active}")
                    print(f"   - 密码哈希: {saved_user.password_hash[:50]}...")
                    
                    # 验证密码是否正确保存
                    print(f"\n🔐 验证密码...")
                    if saved_user.check_password(test_password):
                        print(f"✅ 密码验证通过!（MD5 值正确存储和验证）")
                    else:
                        print(f"❌ 密码验证失败!")
                    
                    # 验证返回的数据
                    if result.get('data'):
                        response_data = result['data']
                        if response_data.get('id') == saved_user.id:
                            print(f"✅ 返回的数据与数据库中的一致!")
                        else:
                            print(f"⚠️  返回的 ID 与数据库不一致")
                    
                    return True, saved_user
                else:
                    print(f"❌ 数据库中没有找到用户数据!")
                    return False, None
            else:
                print(f"❌ 注册失败: {result.get('message', '未知错误')}")
                return False, None
                
        except requests.exceptions.ConnectionError:
            print(f"❌ 连接失败! 请确保后端服务正在运行 (http://localhost:5000)")
            return False, None
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, None

def test_register_with_plain_password():
    """测试使用明文密码注册"""
    print("\n" + "="*80)
    print("🧪 测试 2: 使用明文密码注册")
    print("="*80)
    print(f"📊 使用数据库: MySQL test")
    
    with app.app_context():
        # 生成测试数据
        test_email = generate_test_email()
        test_password = generate_test_password_plain()  # 明文
        test_code = "123456"  # 使用万能验证码
        
        print(f"📧 测试邮箱: {test_email}")
        print(f"🔐 测试密码 (明文): {test_password}")
        print(f"🔑 验证码: {test_code}")
        
        # 检查邮箱是否已存在
        existing_user = User.query.filter_by(email=test_email).first()
        if existing_user:
            print(f"⚠️  邮箱已存在，删除旧记录...")
            db.session.delete(existing_user)
            db.session.commit()
        
        # 直接创建测试验证码（不发送邮件）
        print(f"   🔧 创建测试验证码到数据库（不发送邮件）...")
        create_test_verification_code(test_email, test_code)
        print(f"   ✅ 测试验证码已创建: {test_code}")
        
        # 准备请求数据
        url = "http://localhost:5000/api/register"
        data = {
            "email": test_email,
            "password": test_password,  # 明文
            "verification_code": test_code
        }
        
        print(f"\n📤 发送注册请求...")
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            print(f"📥 响应状态码: {response.status_code}")
            print(f"📥 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if response.status_code == 201 and result.get('success'):
                print(f"\n✅ 注册请求成功!")
                
                # 验证数据是否写入数据库
                print(f"\n🔍 验证数据库中的数据...")
                saved_user = User.query.filter_by(email=test_email).first()
                
                if saved_user:
                    print(f"✅ 用户数据已成功写入数据库!")
                    print(f"   - ID: {saved_user.id}")
                    print(f"   - 邮箱: {saved_user.email}")
                    print(f"   - 角色: {saved_user.role}")
                    
                    # 验证密码是否正确保存
                    print(f"\n🔐 验证密码...")
                    if saved_user.check_password(test_password):
                        print(f"✅ 密码验证通过!（明文密码正确处理）")
                    else:
                        print(f"❌ 密码验证失败!")
                    
                    return True, saved_user
                else:
                    print(f"❌ 数据库中没有找到用户数据!")
                    return False, None
            else:
                print(f"❌ 注册失败: {result.get('message', '未知错误')}")
                return False, None
                
        except requests.exceptions.ConnectionError:
            print(f"❌ 连接失败! 请确保后端服务正在运行 (http://localhost:5000)")
            return False, None
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, None

def test_register_duplicate_email():
    """测试重复邮箱注册"""
    print("\n" + "="*80)
    print("🧪 测试 3: 测试重复邮箱注册（应该失败）")
    print("="*80)
    print(f"📊 使用数据库: MySQL test")
    
    with app.app_context():
        # 先创建一个用户
        test_email = generate_test_email()
        test_password = generate_test_password()
        
        existing_user = User.query.filter_by(email=test_email).first()
        if existing_user:
            db.session.delete(existing_user)
            db.session.commit()
        
        # 直接创建测试验证码（不发送邮件）
        test_code = "123456"
        print(f"   🔧 创建测试验证码到数据库（不发送邮件）...")
        create_test_verification_code(test_email, test_code)
        print(f"   ✅ 测试验证码已创建: {test_code}")
        
        # 第一次注册
        user = User(email=test_email, role='user')
        user.set_password(test_password)
        db.session.add(user)
        db.session.commit()
        print(f"✅ 已创建测试用户: {test_email}")
        
        # 尝试用相同邮箱再次注册
        url = "http://localhost:5000/api/register"
        data = {
            "email": test_email,
            "password": test_password,
            "verification_code": test_code
        }
        
        print(f"\n📤 尝试用相同邮箱注册...")
        try:
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            print(f"📥 响应状态码: {response.status_code}")
            print(f"📥 响应内容: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if response.status_code == 409:
                print(f"✅ 正确拒绝了重复邮箱注册!")
                return True
            else:
                print(f"⚠️  应该返回 409 状态码，但返回了 {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            return False

def check_database_users():
    """查看 MySQL test 数据库中的所有用户"""
    print("\n" + "="*80)
    print("📊 MySQL test 数据库用户统计")
    print("="*80)
    print(f"📊 数据库: MySQL test")
    print(f"🔗 连接: {mysql_user}@{mysql_host}:{mysql_port}/test")
    print()
    
    with app.app_context():
        users = User.query.order_by(User.created_at.desc()).all()
        print(f"总用户数: {len(users)}")
        print()
        
        if users:
            print("用户列表:")
            print("-" * 80)
            for i, user in enumerate(users, 1):
                print(f"{i}. ID: {user.id}")
                print(f"   邮箱: {user.email}")
                print(f"   角色: {user.role}")
                print(f"   创建时间: {user.created_at}")
                print(f"   是否激活: {user.is_active}")
                print("-" * 80)
        else:
            print("⚠️  数据库中没有用户")

def main():
    """主测试函数"""
    print("="*80)
    print("🚀 用户注册功能测试")
    print("="*80)
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 后端地址: http://localhost:5000")
    print()
    
    # 检查服务是否运行
    try:
        response = requests.get("http://localhost:5000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务正在运行")
        else:
            print("⚠️  后端服务响应异常")
    except:
        print("❌ 无法连接到后端服务!")
        print("💡 请先启动后端服务: python app.py")
        return
    
    print()
    
    # 执行测试
    results = []
    
    # 测试 1: MD5 密码注册
    success1, user1 = test_register_with_md5_password()
    results.append(("MD5密码注册", success1))
    
    # 测试 2: 明文密码注册
    success2, user2 = test_register_with_plain_password()
    results.append(("明文密码注册", success2))
    
    # 测试 3: 重复邮箱
    success3 = test_register_duplicate_email()
    results.append(("重复邮箱检测", success3))
    
    # 显示数据库统计
    check_database_users()
    
    # 测试总结
    print("\n" + "="*80)
    print("📊 测试总结")
    print("="*80)
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {test_name}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\n总计: {passed}/{total} 通过")
    print("="*80)

if __name__ == "__main__":
    main()

