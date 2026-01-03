"""
测试身份验证 API 的脚本
"""
import sys
import os
import io
from datetime import datetime

# Windows 控制台编码修复
if sys.platform == 'win32':
    try:
        # 检查是否已经包装过，避免重复包装导致文件关闭
        if not isinstance(sys.stdout, io.TextIOWrapper) or sys.stdout.encoding.lower() != 'utf-8':
            # 保存原始的 stdout
            _original_stdout = sys.stdout
            _original_stderr = sys.stderr
            # 包装为 UTF-8 编码
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except (AttributeError, OSError):
        # 如果无法包装（例如已经在其他地方包装过），忽略错误
        pass

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

import requests
import json

# API 基础 URL
BASE_URL = "http://localhost:5000/api"

# 测试用户数据
TEST_EMAIL = f"test_auth_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com"
TEST_PASSWORD = "test123456"

# 存储 Token
access_token = None
refresh_token = None


def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def test_register():
    """测试注册"""
    print_section("1. 测试用户注册")
    
    global TEST_EMAIL
    
    # 创建测试验证码（模拟）
    from src.app import app
    from src.models import db, EmailVerification
    from datetime import timedelta
    
    with app.app_context():
        verification = EmailVerification(
            email=TEST_EMAIL,
            code="123456",
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        db.session.add(verification)
        db.session.commit()
    
    data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "verification_code": "123456"
    }
    
    response = requests.post(f"{BASE_URL}/register", json=data)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    assert response.status_code in [201, 409], "注册失败"
    return response.status_code == 201


def test_login():
    """测试登录"""
    print_section("2. 测试用户登录")
    
    global access_token, refresh_token
    
    data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/login", json=data)
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    assert response.status_code == 200, "登录失败"
    assert result['success'], "登录失败"
    
    access_token = result['data']['access_token']
    refresh_token = result['data']['refresh_token']
    
    print(f"\n✅ Access Token: {access_token[:50]}...")
    print(f"✅ Refresh Token: {refresh_token[:50]}...")
    
    return True


def test_get_current_user():
    """测试获取当前用户信息"""
    print_section("3. 测试获取当前用户信息（需要认证）")
    
    global access_token
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    assert response.status_code == 200, "获取用户信息失败"
    return True


def test_protected_route_without_token():
    """测试未携带 Token 访问受保护的路由"""
    print_section("4. 测试未携带 Token 访问受保护的路由")
    
    response = requests.get(f"{BASE_URL}/users/me")
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    assert response.status_code == 401, "应该返回 401 未授权"
    return True


def test_refresh_token():
    """测试刷新 Token"""
    print_section("5. 测试刷新 Token")
    
    global refresh_token, access_token
    
    data = {
        "refresh_token": refresh_token
    }
    
    response = requests.post(f"{BASE_URL}/refresh-token", json=data)
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    assert response.status_code == 200, "刷新 Token 失败"
    assert result['success'], "刷新 Token 失败"
    
    # 更新 Access Token
    new_access_token = result['data']['access_token']
    print(f"\n✅ 新的 Access Token: {new_access_token[:50]}...")
    
    # 验证新 Token 是否可用
    headers = {
        "Authorization": f"Bearer {new_access_token}"
    }
    test_response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    assert test_response.status_code == 200, "新 Token 无效"
    
    access_token = new_access_token
    return True


def test_invalid_token():
    """测试无效 Token"""
    print_section("6. 测试无效 Token")
    
    headers = {
        "Authorization": "Bearer invalid_token_here"
    }
    
    response = requests.get(f"{BASE_URL}/users/me", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    assert response.status_code == 401, "应该返回 401"
    return True


def test_admin_route_as_user():
    """测试普通用户访问管理员路由"""
    print_section("7. 测试普通用户访问管理员路由")
    
    global access_token
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(f"{BASE_URL}/users", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    # 普通用户应该没有权限
    assert response.status_code == 403, "应该返回 403 权限不足"
    return True


def main():
    """运行所有测试"""
    print("\n" + "=" * 80)
    print(" 🧪 身份验证 API 测试")
    print("=" * 80)
    
    try:
        # 1. 注册用户
        if not test_register():
            print("\n⚠️  用户可能已存在，继续测试...")
        
        # 2. 登录
        test_login()
        
        # 3. 获取当前用户
        test_get_current_user()
        
        # 4. 未携带 Token
        test_protected_route_without_token()
        
        # 5. 刷新 Token
        test_refresh_token()
        
        # 6. 无效 Token
        test_invalid_token()
        
        # 7. 权限测试
        test_admin_route_as_user()
        
        print_section("✅ 所有测试通过！")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

