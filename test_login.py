#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试登录功能
"""

import requests
import json

def test_login():
    """测试登录"""
    url = 'http://localhost:5000/api/login'
    headers = {'Content-Type': 'application/json'}

    # 测试用MD5密码登录
    data = {
        'email': '123456789@qq.com',
        'password': 'e10adc3949ba59abbe56e057f20f883e'
    }

    print('测试登录...')
    print(f'URL: {url}')
    print(f'数据: {json.dumps(data, indent=2)}')

    try:
        response = requests.post(url, json=data, headers=headers)
        print(f'\n响应状态码: {response.status_code}')
        print(f'响应内容: {response.text}')

        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print('✅ 登录成功！')
                return True
            else:
                print(f'❌ 登录失败: {result.get("message")}')
        else:
            print(f'❌ 请求失败，状态码: {response.status_code}')

    except Exception as e:
        print(f'❌ 请求异常: {e}')

    return False

if __name__ == '__main__':
    test_login()
