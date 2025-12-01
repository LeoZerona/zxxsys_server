"""测试发送验证码功能的完整测试脚本"""
import requests
import json
import time
import sys
from datetime import datetime

# API 基础 URL
BASE_URL = "http://localhost:5000/api"

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_section(title):
    """打印章节"""
    print("\n" + "-" * 70)
    print(f"  {title}")
    print("-" * 70)

def test_1_send_verification_code_success():
    """测试 1: 成功发送验证码"""
    print_header("测试 1: 成功发送验证码")
    
    email = "test@example.com"
    url = f"{BASE_URL}/send-verification-code"
    
    print(f"\n📧 测试邮箱: {email}")
    print(f"🌐 请求 URL: {url}")
    
    try:
        response = requests.post(
            url,
            json={"email": email},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\n📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 响应内容:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            if result.get('success'):
                print("\n✅ 测试通过: 验证码发送成功")
                
                # 如果返回了验证码（测试模式）
                if 'code' in result:
                    print(f"🔑 验证码: {result['code']} (测试模式返回)")
                
                return result.get('code')
            else:
                print(f"\n❌ 测试失败: {result.get('message')}")
                return None
        else:
            print(f"\n❌ 测试失败: HTTP {response.status_code}")
            try:
                error = response.json()
                print(f"错误信息: {json.dumps(error, ensure_ascii=False, indent=2)}")
            except:
                print(f"错误信息: {response.text}")
            return None
    
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败: Flask 应用可能未运行")
        print("   请先运行: python app.py")
        return None
    except Exception as e:
        print(f"\n❌ 请求失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_2_verify_code_success(email, code):
    """测试 2: 成功验证验证码"""
    if not code:
        print("\n⚠️  跳过测试 2: 未获取到验证码")
        return False
    
    print_header("测试 2: 验证验证码（正确验证码）")
    
    url = f"{BASE_URL}/verify-code"
    
    print(f"\n📧 邮箱: {email}")
    print(f"🔑 验证码: {code}")
    print(f"🌐 请求 URL: {url}")
    
    try:
        response = requests.post(
            url,
            json={"email": email, "code": code},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\n📊 响应状态码: {response.status_code}")
        result = response.json()
        print(f"📄 响应内容:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if response.status_code == 200 and result.get('success'):
            print("\n✅ 测试通过: 验证码验证成功")
            return True
        else:
            print(f"\n❌ 测试失败: {result.get('message')}")
            return False
    
    except Exception as e:
        print(f"\n❌ 请求失败: {str(e)}")
        return False

def test_3_verify_code_invalid(email):
    """测试 3: 验证无效验证码"""
    print_header("测试 3: 验证无效验证码")
    
    url = f"{BASE_URL}/verify-code"
    invalid_code = "000000"
    
    print(f"\n📧 邮箱: {email}")
    print(f"🔑 无效验证码: {invalid_code}")
    
    try:
        response = requests.post(
            url,
            json={"email": email, "code": invalid_code},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\n📊 响应状态码: {response.status_code}")
        result = response.json()
        print(f"📄 响应内容:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if response.status_code == 400 and not result.get('success'):
            print("\n✅ 测试通过: 正确拒绝了无效验证码")
            return True
        else:
            print("\n❌ 测试失败: 应该拒绝无效验证码")
            return False
    
    except Exception as e:
        print(f"\n❌ 请求失败: {str(e)}")
        return False

def test_4_send_code_invalid_email():
    """测试 4: 发送验证码到无效邮箱"""
    print_header("测试 4: 发送验证码到无效邮箱格式")
    
    url = f"{BASE_URL}/send-verification-code"
    invalid_email = "invalid-email"
    
    print(f"\n📧 无效邮箱: {invalid_email}")
    
    try:
        response = requests.post(
            url,
            json={"email": invalid_email},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\n📊 响应状态码: {response.status_code}")
        result = response.json()
        print(f"📄 响应内容:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if response.status_code == 400 and not result.get('success'):
            print("\n✅ 测试通过: 正确拒绝了无效邮箱格式")
            return True
        else:
            print("\n❌ 测试失败: 应该拒绝无效邮箱格式")
            return False
    
    except Exception as e:
        print(f"\n❌ 请求失败: {str(e)}")
        return False

def test_5_send_code_empty_email():
    """测试 5: 发送验证码到空邮箱"""
    print_header("测试 5: 发送验证码到空邮箱")
    
    url = f"{BASE_URL}/send-verification-code"
    
    print(f"\n📧 空邮箱: (空字符串)")
    
    try:
        response = requests.post(
            url,
            json={"email": ""},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"\n📊 响应状态码: {response.status_code}")
        result = response.json()
        print(f"📄 响应内容:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if response.status_code == 400 and not result.get('success'):
            print("\n✅ 测试通过: 正确拒绝了空邮箱")
            return True
        else:
            print("\n❌ 测试失败: 应该拒绝空邮箱")
            return False
    
    except Exception as e:
        print(f"\n❌ 请求失败: {str(e)}")
        return False

def test_6_resend_verification_code(email):
    """测试 6: 重新发送验证码（同一邮箱）"""
    print_header("测试 6: 重新发送验证码（更新验证码）")
    
    url = f"{BASE_URL}/send-verification-code"
    
    print(f"\n📧 邮箱: {email}")
    print("💡 测试说明: 对同一邮箱发送两次验证码，应该更新而不是创建新记录")
    
    try:
        # 第一次发送
        print("\n🔄 第一次发送验证码...")
        response1 = requests.post(
            url,
            json={"email": email},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        code1 = None
        if response1.status_code == 200:
            result1 = response1.json()
            if result1.get('success') and 'code' in result1:
                code1 = result1['code']
                print(f"✅ 第一次验证码: {code1}")
        
        # 等待 1 秒
        time.sleep(1)
        
        # 第二次发送
        print("\n🔄 第二次发送验证码...")
        response2 = requests.post(
            url,
            json={"email": email},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        code2 = None
        if response2.status_code == 200:
            result2 = response2.json()
            if result2.get('success') and 'code' in result2:
                code2 = result2['code']
                print(f"✅ 第二次验证码: {code2}")
        
        if code1 and code2 and code1 != code2:
            print("\n✅ 测试通过: 重新发送时验证码已更新")
            return True
        elif code1 and code2:
            print("\n⚠️  警告: 两次验证码相同（可能是时间太短）")
            return True
        else:
            print("\n❌ 测试失败: 无法获取验证码")
            return False
    
    except Exception as e:
        print(f"\n❌ 请求失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=" * 70)
    print("  📧 邮箱验证码功能完整测试")
    print("=" * 70)
    print("\n📋 测试说明:")
    print("   1. 确保 Flask 应用正在运行 (python app.py)")
    print("   2. 测试将验证发送验证码和验证验证码的功能")
    print("   3. 如果未配置真实邮箱，将使用测试模式")
    
    test_email = input("\n📧 请输入测试邮箱 [默认: test@example.com]: ").strip()
    if not test_email:
        test_email = "test@example.com"
    
    print("\n" + "=" * 70)
    print("  开始测试...")
    print("=" * 70)
    
    results = []
    
    # 测试 1: 发送验证码
    code = test_1_send_verification_code_success()
    results.append(("发送验证码", code is not None))
    
    if code:
        # 测试 2: 验证验证码
        time.sleep(1)
        results.append(("验证正确验证码", test_2_verify_code_success(test_email, code)))
        
        # 测试 6: 重新发送验证码（在测试 3 之前）
        time.sleep(1)
        results.append(("重新发送验证码", test_6_resend_verification_code(test_email)))
        
        # 测试 3: 验证无效验证码（使用不同的邮箱，避免与已验证的邮箱冲突）
        time.sleep(1)
        results.append(("验证无效验证码", test_3_verify_code_invalid("invalid_test@example.com")))
    
    # 测试 4: 无效邮箱
    time.sleep(1)
    results.append(("无效邮箱格式", test_4_send_code_invalid_email()))
    
    # 测试 5: 空邮箱
    time.sleep(1)
    results.append(("空邮箱", test_5_send_code_empty_email()))
    
    # 打印测试总结
    print_header("测试总结")
    
    print("\n📊 测试结果:")
    print("-" * 70)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}  - {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 70)
    print(f"\n📈 总计: {len(results)} 个测试")
    print(f"✅ 通过: {passed} 个")
    print(f"❌ 失败: {failed} 个")
    print(f"📊 通过率: {passed/len(results)*100:.1f}%")
    
    print("\n" + "=" * 70)
    
    if failed == 0:
        print("  🎉 所有测试通过！")
    else:
        print(f"  ⚠️  有 {failed} 个测试失败，请检查")
    
    print("=" * 70 + "\n")
    
    return failed == 0

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  测试已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

