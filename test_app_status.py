#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Flask应用状态
"""

import requests
import time

def test_app_status():
    """测试应用状态"""
    url = 'http://localhost:5000/api/health'

    print('正在测试Flask应用状态...')
    print(f'测试URL: {url}')

    try:
        response = requests.get(url, timeout=5)
        print(f'连接成功! 状态码: {response.status_code}')

        if response.status_code == 200:
            result = response.json()
            print('Flask应用已启动并运行正常!')
            print(f'响应: {result}')
            return True
        else:
            print(f'响应异常: {response.text}')
            return False

    except requests.exceptions.RequestException as e:
        print(f'连接失败: {e}')
        print('Flask应用可能还没有启动或端口不正确')
        return False

if __name__ == '__main__':
    test_app_status()
