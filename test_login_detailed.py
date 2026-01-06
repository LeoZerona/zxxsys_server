#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
详细测试登录功能
"""
import requests
import json
import sys

# 设置控制台编码为UTF-8（Windows兼容性）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def test_login():
    """测试登录"""
    url = 'http://localhost:5000/api/login'
    headers = {'Content-Type': 'application/json'}
    
    # 测试用MD5密码登录
    data = {
        'email': '123456789@qq.com',
        'password': 'e10adc3949ba59abbe56e057f20f883e'
    }
    
    print('=' * 80)
    print('测试登录接口')
    print('=' * 80)
    print(f'URL: {url}')
    print(f'请求参数:')
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print('-' * 80)
    
    try:
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f'\n响应状态码: {response.status_code}')
        print('响应内容:')
        
        # 格式化JSON输出
        try:
            result = response.json()
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            print('\n' + '-' * 80)
            if response.status_code == 200:
                if result.get('success'):
                    print('[成功] 登录成功！')
                    print(f"用户ID: {result.get('data', {}).get('user', {}).get('id')}")
                    print(f"用户邮箱: {result.get('data', {}).get('user', {}).get('email')}")
                    print(f"用户角色: {result.get('data', {}).get('role')}")
                    print(f"Access Token: {result.get('data', {}).get('access_token', '')[:50]}...")
                    print(f"权限数量: {len(result.get('data', {}).get('permissions', []))}")
                    print(f"菜单数量: {len(result.get('data', {}).get('menus', []))}")
                    return True
                else:
                    print(f'[失败] 登录失败: {result.get("message")}')
                    if result.get('code'):
                        print(f'错误代码: {result.get("code")}')
                    if result.get('requires_captcha'):
                        print('需要验证码')
            else:
                print(f'[失败] 请求失败，状态码: {response.status_code}')
                print(f'错误信息: {result.get("message", "未知错误")}')
        except json.JSONDecodeError:
            print(response.text)
            print('[错误] 响应不是有效的JSON格式')
            
    except requests.exceptions.ConnectionError:
        print('[错误] 无法连接到服务器，请确保服务器正在运行')
        print('提示: 运行 python src/app.py 启动服务器')
    except requests.exceptions.Timeout:
        print('[错误] 请求超时')
    except Exception as e:
        print(f'[错误] 请求异常: {e}')
        import traceback
        traceback.print_exc()
    
    print('=' * 80)
    return False

if __name__ == '__main__':
    test_login()

