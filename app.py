"""
Flask 应用入口文件
"""
from src.app import app, socketio
import socket
import sys
import os

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 Flask 后端服务启动中...")
    print("="*80)
    
    # 检测端口是否可用
    def is_port_available(port):
        """检测端口是否可用"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return True
        except OSError:
            return False
    
    # 尝试的端口列表
    default_port = 5000
    ports_to_try = [default_port, 5001, 5002, 8000, 8080]
    
    selected_port = None
    for port in ports_to_try:
        if is_port_available(port):
            selected_port = port
            break
    
    if selected_port is None:
        print("❌ 错误: 所有尝试的端口都被占用")
        print(f"   尝试的端口: {', '.join(map(str, ports_to_try))}")
        print("   请关闭占用端口的程序或手动指定其他端口")
        sys.exit(1)
    
    # 允许从环境变量配置监听地址，默认监听 0.0.0.0 以支持局域网访问
    # 如果需要仅本地访问，可以设置环境变量 HOST=127.0.0.1
    host = os.environ.get('HOST', '0.0.0.0')
    
    # 获取本机IP地址（用于局域网访问）
    def get_local_ip():
        """获取本机局域网IP地址"""
        try:
            # 创建一个UDP socket来获取本机IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                # 连接到一个远程地址（不需要实际连接）
                s.connect(('8.8.8.8', 80))
                ip = s.getsockname()[0]
            except Exception:
                ip = '127.0.0.1'
            finally:
                s.close()
            return ip
        except Exception:
            return '127.0.0.1'
    
    local_ip = get_local_ip()
    
    if selected_port != default_port:
        print(f"⚠️  端口 {default_port} 被占用，使用端口 {selected_port}")
    
    print(f"\n📍 本地访问地址:")
    print(f"   服务地址: http://localhost:{selected_port}")
    print(f"   API 路径: http://localhost:{selected_port}/api")
    print(f"   WebSocket: ws://localhost:{selected_port}/socket.io/")
    
    if local_ip != '127.0.0.1':
        print(f"\n🌐 局域网访问地址:")
        if host == '0.0.0.0':
            print(f"   服务地址: http://{local_ip}:{selected_port}")
            print(f"   API 路径: http://{local_ip}:{selected_port}/api")
            print(f"   WebSocket: ws://{local_ip}:{selected_port}/socket.io/")
            print(f"   ✅ 已启用局域网访问（监听 0.0.0.0）")
        else:
            print(f"   本机IP: {local_ip}")
            print(f"   ⚠️  当前仅允许本地访问（监听 127.0.0.1）")
            print(f"   💡 如需局域网访问，请修改代码将 host 设置为 '0.0.0.0'")
    
    print(f"\n🔧 服务器配置:")
    print(f"   监听地址: {host}")
    print(f"   监听端口: {selected_port}")
    
    # 显示万能验证码信息（仅开发环境）
    universal_code = app.config.get('UNIVERSAL_VERIFICATION_CODE', '')
    if universal_code:
        print("-"*80)
        print(f"🔓 万能验证码已启用: {universal_code}")
        print(f"   ⚠️  此验证码可以验证任何邮箱（仅用于测试）")
        print(f"   💡 生产环境请设置 UNIVERSAL_VERIFICATION_CODE='' 禁用")
    
    print("="*80)
    print("📝 请求日志已启用，所有 API 请求将在控制台显示")
    print("="*80 + "\n")
    
    try:
        # 使用 SocketIO 运行应用（支持 WebSocket）
        # threading 模式兼容性更好，同时支持 HTTP 请求和 WebSocket
        # 注意：在 threading 模式下禁用重载器以避免 WERKZEUG_SERVER_FD 错误
        
        # 确保 WERKZEUG_SERVER_FD 环境变量不存在（避免 KeyError）
        if 'WERKZEUG_SERVER_FD' in os.environ:
            del os.environ['WERKZEUG_SERVER_FD']
        
        # 在 threading 模式下，使用更简单的启动方式
        # 注意：debug=True 在 threading 模式下可能导致问题，改为 False
        socketio.run(
            app, 
            debug=False,  # threading 模式下禁用 debug 模式以避免重载器问题
            host=host, 
            port=selected_port, 
            allow_unsafe_werkzeug=True,
            use_reloader=False  # 禁用重载器以避免 WERKZEUG_SERVER_FD 错误
        )
    except (OSError, KeyError, Exception) as e:
        print(f"\n❌ 启动失败: {str(e)}")
        print(f"   错误类型: {type(e).__name__}")
        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()
        print("\n💡 解决方案:")
        print("   1. 检查端口是否被其他程序占用")
        print("   2. 尝试以管理员权限运行")
        print("   3. 检查防火墙设置")
        print("   4. 尝试使用其他端口（修改代码中的 ports_to_try 列表）")
        if isinstance(e, KeyError):
            print("   5. 如果仍然报错，请重启终端或IDE后重试")
        print("   6. 检查 Flask-SocketIO 版本是否兼容")
        sys.exit(1)

