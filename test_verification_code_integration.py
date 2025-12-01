"""集成测试：验证码发送和验证的完整流程"""
import requests
import json
import time

BASE_URL = "http://localhost:5000/api"

class TestVerificationCodeIntegration:
    """验证码功能集成测试"""
    
    def __init__(self):
        self.test_email = "integration_test@example.com"
        self.verification_code = None
    
    def print_test(self, test_name, description=""):
        """打印测试信息"""
        print("\n" + "=" * 70)
        print(f"  测试: {test_name}")
        if description:
            print(f"  说明: {description}")
        print("=" * 70)
    
    def test_complete_flow(self):
        """完整流程测试：发送验证码 → 验证验证码"""
        print("\n" + "=" * 70)
        print("  📧 验证码完整流程集成测试")
        print("=" * 70)
        print(f"\n📧 测试邮箱: {self.test_email}")
        
        # 步骤 1: 发送验证码
        self.print_test("步骤 1: 发送验证码", "向邮箱发送验证码")
        
        try:
            response = requests.post(
                f"{BASE_URL}/send-verification-code",
                json={"email": self.test_email},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"\n📊 状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"📄 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
                
                if result.get('success'):
                    print("\n✅ 验证码发送成功")
                    
                    # 获取验证码
                    if 'code' in result:
                        self.verification_code = result['code']
                        print(f"🔑 验证码: {self.verification_code}")
                    
                    # 步骤 2: 验证验证码
                    if self.verification_code:
                        time.sleep(1)
                        return self.test_verify_code()
                    else:
                        print("\n⚠️  未获取到验证码，跳过验证步骤")
                        return True
                else:
                    print(f"\n❌ 发送失败: {result.get('message')}")
                    return False
            else:
                print(f"\n❌ HTTP 错误: {response.status_code}")
                return False
        
        except requests.exceptions.ConnectionError:
            print("\n❌ 连接失败: Flask 应用可能未运行")
            print("   请先运行: python app.py")
            return False
        except Exception as e:
            print(f"\n❌ 请求失败: {str(e)}")
            return False
    
    def test_verify_code(self):
        """验证验证码"""
        self.print_test("步骤 2: 验证验证码", "使用获取的验证码进行验证")
        
        if not self.verification_code:
            print("\n⚠️  没有验证码，跳过验证")
            return False
        
        try:
            response = requests.post(
                f"{BASE_URL}/verify-code",
                json={
                    "email": self.test_email,
                    "code": self.verification_code
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            print(f"\n📊 状态码: {response.status_code}")
            result = response.json()
            print(f"📄 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if response.status_code == 200 and result.get('success'):
                print("\n✅ 验证码验证成功")
                return True
            else:
                print(f"\n❌ 验证失败: {result.get('message')}")
                return False
        
        except Exception as e:
            print(f"\n❌ 请求失败: {str(e)}")
            return False
    
    def test_error_cases(self):
        """错误情况测试"""
        print("\n" + "=" * 70)
        print("  ⚠️  错误情况测试")
        print("=" * 70)
        
        error_cases = [
            {
                "name": "无效邮箱格式",
                "endpoint": "/send-verification-code",
                "data": {"email": "invalid-email"},
                "expected_status": 400
            },
            {
                "name": "空邮箱",
                "endpoint": "/send-verification-code",
                "data": {"email": ""},
                "expected_status": 400
            },
            {
                "name": "无效验证码",
                "endpoint": "/verify-code",
                "data": {"email": self.test_email, "code": "000000"},
                "expected_status": 400
            },
            {
                "name": "验证码缺失",
                "endpoint": "/verify-code",
                "data": {"email": self.test_email},
                "expected_status": 400
            }
        ]
        
        results = []
        
        for case in error_cases:
            print(f"\n📋 测试: {case['name']}")
            try:
                response = requests.post(
                    f"{BASE_URL}{case['endpoint']}",
                    json=case['data'],
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                print(f"   状态码: {response.status_code} (期望: {case['expected_status']})")
                
                if response.status_code == case['expected_status']:
                    print(f"   ✅ 通过")
                    results.append(True)
                else:
                    print(f"   ❌ 失败")
                    results.append(False)
                
                time.sleep(0.5)
            
            except Exception as e:
                print(f"   ❌ 错误: {str(e)}")
                results.append(False)
        
        return all(results)

def main():
    """运行所有测试"""
    tester = TestVerificationCodeIntegration()
    
    print("\n" + "=" * 70)
    print("  🧪 验证码功能集成测试套件")
    print("=" * 70)
    print("\n📋 测试内容:")
    print("   1. 完整流程测试（发送 → 验证）")
    print("   2. 错误情况测试")
    print("\n⚠️  提示: 确保 Flask 应用正在运行")
    
    input("\n按 Enter 键开始测试...")
    
    # 完整流程测试
    flow_result = tester.test_complete_flow()
    
    # 错误情况测试
    error_result = tester.test_error_cases()
    
    # 总结
    print("\n" + "=" * 70)
    print("  📊 测试总结")
    print("=" * 70)
    print(f"\n✅ 完整流程测试: {'通过' if flow_result else '失败'}")
    print(f"✅ 错误情况测试: {'通过' if error_result else '失败'}")
    
    if flow_result and error_result:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败，请检查")
    
    print("=" * 70 + "\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  测试已取消")
    except Exception as e:
        print(f"\n\n❌ 测试出错: {str(e)}")
        import traceback
        traceback.print_exc()

