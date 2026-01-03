"""
邮箱相关路由（发送验证码、验证验证码等）
"""
from flask import request, jsonify
import re
from src.config import Config
from src.services.email_service import send_verification_code, verify_code


def register_email_routes(app):
    """注册邮箱相关的路由"""
    
    @app.route('/api/send-verification-code', methods=['POST'])
    def send_code():
        """发送邮箱验证码"""
        try:
            data = request.get_json()
            
            print("📧 发送验证码接口被调用")
            print(f"   邮箱: {data.get('email', '未提供') if data else '无数据'}")
            
            if not data:
                print("   ⚠️ 错误: 请求数据为空")
                return jsonify({
                    'success': False,
                    'message': '请求数据不能为空'
                }), 400
            
            email = data.get('email', '').strip()
            
            if not email:
                print("   ⚠️ 错误: 邮箱为空")
                return jsonify({
                    'success': False,
                    'message': '邮箱不能为空'
                }), 400
            
            if not re.match(Config.EMAIL_REGEX, email):
                print(f"   ⚠️ 错误: 邮箱格式不正确 - {email}")
                return jsonify({
                    'success': False,
                    'message': '邮箱格式不正确'
                }), 400
            
            print(f"   ✅ 邮箱格式验证通过，开始发送验证码到: {email}")
            result = send_verification_code(email)
            
            if result.get('success'):
                print(f"   ✅ 验证码发送成功！")
                if 'code' in result:
                    print(f"   🔑 验证码: {result['code']} (测试模式)")
            else:
                print(f"   ❌ 验证码发送失败: {result.get('message', '未知错误')}")
            
            if result['success']:
                # 开发环境可以返回验证码，生产环境应移除
                response_data = {
                    'success': True,
                    'message': result['message']
                }
                # 如果配置了测试模式或开发环境，可以返回验证码
                if 'code' in result:
                    response_data['code'] = result['code']  # 仅用于测试
                
                return jsonify(response_data), 200
            else:
                # 如果是频率限制，返回 429 状态码
                status_code = 429 if 'cooldown_seconds' in result else 500
                return jsonify(result), status_code
        
        except Exception as e:
            print(f"   ❌ 发送验证码过程中发生异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'发送验证码失败: {str(e)}'
            }), 500

    @app.route('/api/verify-code', methods=['POST'])
    def verify_verification_code():
        """验证邮箱验证码"""
        try:
            data = request.get_json()
            
            print("🔍 验证验证码接口被调用")
            if data:
                email = data.get('email', '').strip()
                code = data.get('code', '').strip()
                print(f"   邮箱: {email}")
                print(f"   验证码: {code[:2]}**" if code else "未提供")
            
            if not data:
                print("   ⚠️ 错误: 请求数据为空")
                return jsonify({
                    'success': False,
                    'message': '请求数据不能为空'
                }), 400
            
            email = data.get('email', '').strip()
            code = data.get('code', '').strip()
            
            if not email or not code:
                print("   ⚠️ 错误: 邮箱或验证码为空")
                return jsonify({
                    'success': False,
                    'message': '邮箱和验证码不能为空'
                }), 400
            
            print(f"   🔍 开始验证验证码...")
            result = verify_code(email, code)
            
            if result['success']:
                print(f"   ✅ 验证码验证成功！")
                return jsonify(result), 200
            else:
                print(f"   ❌ 验证码验证失败: {result.get('message', '未知错误')}")
                return jsonify(result), 400
        
        except Exception as e:
            print(f"   ❌ 验证过程中发生异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'验证失败: {str(e)}'
            }), 500

