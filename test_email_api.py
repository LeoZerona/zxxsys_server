"""测试邮箱验证码 API 的脚本"""
import requests
import json
import time

# API 基础 URL
BASE_URL = "http://localhost:5000/api"

def test_send_verification_code(email):
    """测试发送验证码"""
    print("=" * 60)
    print("测试发送验证码")
    print("=" * 60)
    
    url = f"{BASE_URL}/send-verification-code"
    data = {
        "email": email
    }
    
    print(f"\n请求 URL: {url}")
    print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            url,
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容:")
        
        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if response.status_code == 200 and result.get('success'):
            print("\n✓ 发送验证码成功！")
            if 'code' in result:
                print(f"验证码: {result['code']} (测试模式返回的验证码)")
            return result.get('code')
        else:
            print("\n✗ 发送验证码失败")
            return None
    
    except requests.exceptions.ConnectionError:
        print("\n✗ 连接失败！请确保 Flask 应用正在运行 (python app.py)")
        return None
    except Exception as e:
        print(f"\n✗ 请求失败: {str(e)}")
        return None

def test_verify_code(email, code):
    """测试验证验证码"""
    print("\n" + "=" * 60)
    print("测试验证验证码")
    print("=" * 60)
    
    url = f"{BASE_URL}/verify-code"
    data = {
        "email": email,
        "code": code
    }
    
    print(f"\n请求 URL: {url}")
    print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(
            url,
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"\n响应状态码: {response.status_code}")
        print(f"响应内容:")
        
        result = response.json()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if response.status_code == 200 and result.get('success'):
            print("\n✓ 验证码验证成功！")
            return True
        else:
            print("\n✗ 验证码验证失败")
            return False
    
    except requests.exceptions.ConnectionError:
        print("\n✗ 连接失败！请确保 Flask 应用正在运行 (python app.py)")
        return False
    except Exception as e:
        print(f"\n✗ 请求失败: {str(e)}")
        return False

def test_invalid_email():
    """测试无效邮箱"""
    print("\n" + "=" * 60)
    print("测试无效邮箱格式")
    print("=" * 60)
    
    url = f"{BASE_URL}/send-verification-code"
    data = {
        "email": "invalid-email"
    }
    
    try:
        response = requests.post(url, json=data)
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 400:
            print("\n✓ 正确拒绝了无效邮箱")
        else:
            print("\n✗ 应该拒绝无效邮箱")
    
    except Exception as e:
        print(f"\n✗ 请求失败: {str(e)}")

def test_invalid_code(email):
    """测试无效验证码"""
    print("\n" + "=" * 60)
    print("测试无效验证码")
    print("=" * 60)
    
    url = f"{BASE_URL}/verify-code"
    data = {
        "email": email,
        "code": "000000"
    }
    
    try:
        response = requests.post(url, json=data)
        result = response.json()
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        if response.status_code == 400:
            print("\n✓ 正确拒绝了无效验证码")
        else:
            print("\n✗ 应该拒绝无效验证码")
    
    except Exception as e:
        print(f"\n✗ 请求失败: {str(e)}")

def main():
    """主测试函数"""
    print("=" * 60)
    print("邮箱验证码功能测试")
    print("=" * 60)
    print("\n提示:")
    print("1. 确保 Flask 应用正在运行 (python app.py)")
    print("2. 如果没有配置真实邮箱，验证码会打印到控制台（测试模式）")
    print("3. 测试模式下，API 会返回验证码，方便测试")
    
    # 测试邮箱
    test_email = input("\n请输入测试邮箱 [默认: test@example.com]: ").strip() or "test@example.com"
    
    print("\n" + "=" * 60)
    print("开始测试...")
    print("=" * 60)
    
    # 1. 测试发送验证码
    code = test_send_verification_code(test_email)
    
    if code:
        # 等待一下
        time.sleep(1)
        
        # 2. 测试验证验证码
        print("\n请输入验证码进行验证:")
        print(f"  从 API 返回的验证码: {code}")
        
        verify_code_input = input("\n请输入验证码 [直接回车使用上面的验证码]: ").strip() or code
        
        test_verify_code(test_email, verify_code_input)
        
        # 3. 测试无效验证码
        time.sleep(1)
        test_invalid_code(test_email)
    
    # 4. 测试无效邮箱
    time.sleep(1)
    test_invalid_email()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n\n测试出错: {str(e)}")
        import traceback
        traceback.print_exc()

