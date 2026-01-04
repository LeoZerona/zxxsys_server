from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import re
import logging
from datetime import datetime
from src.config import Config
from src.models import db, User, LoginAttempt  # 导入所有模型以确保表被创建
from src.services.email_service import init_mail
from src.routes.auth import register_route as register_auth_route
from src.routes.email import register_email_routes
from src.routes.user import register_user_routes
from src.routes.question import register_question_routes
from src.routes.question_dedup import register_question_dedup_routes
from src.middleware.auth_middleware import init_auth_middleware

app = Flask(__name__)
app.config.from_object(Config)

# 初始化 SocketIO（支持 WebSocket）
socketio = SocketIO(
    app,
    cors_allowed_origins="*" if app.config.get('CORS_ALLOW_ALL_ORIGINS') else app.config.get('CORS_ORIGINS', []),
    async_mode='eventlet',
    logger=True,
    engineio_logger=True
)

# 配置日志
# 设置控制台编码为 UTF-8（Windows 兼容性）
import sys
import io
if sys.platform == 'win32':
    try:
        # 检查是否已经包装过，避免重复包装导致文件关闭
        if not isinstance(sys.stdout, io.TextIOWrapper) or (hasattr(sys.stdout, 'encoding') and sys.stdout.encoding.lower() != 'utf-8'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if not isinstance(sys.stderr, io.TextIOWrapper) or (hasattr(sys.stderr, 'encoding') and sys.stderr.encoding.lower() != 'utf-8'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except (AttributeError, OSError, ValueError):
        # 如果无法包装（例如已经在其他地方包装过，或文件已关闭），忽略错误
        pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 请求日志钩子 - 记录所有 API 请求
@app.before_request
def log_request_info():
    """记录所有 API 请求的详细信息"""
    if request.path.startswith('/api/'):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        method = request.method
        path = request.path
        remote_addr = request.remote_addr
        
        # 获取请求数据（仅在 POST/PUT 请求中）
        request_data = None
        if request.is_json:
            try:
                request_data = request.get_json()
            except:
                request_data = "无法解析 JSON"
        
        # 打印请求信息（带分隔线和颜色标记）
        print("\n" + "="*80)
        print(f"🟢 [{timestamp}] 收到请求")
        print(f"📍 路径: {method} {path}")
        print(f"🌐 IP: {remote_addr}")
        if request_data:
            print(f"📦 请求数据: {request_data}")
        print("="*80)
        
        # 同时记录到日志
        logger.info(f"请求: {method} {path} | IP: {remote_addr} | 数据: {request_data}")

@app.after_request
def log_response_info(response):
    """记录响应信息并处理 CORS"""
    if request.path.startswith('/api/'):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status_code = response.status_code
        status_emoji = "✅" if 200 <= status_code < 300 else "❌" if status_code >= 400 else "ℹ️"
        
        # 记录 CORS 请求来源（用于调试）
        origin = request.headers.get('Origin')
        cors_info = f" | CORS来源: {origin}" if origin else ""
        
        print(f"{status_emoji} [{timestamp}] 响应: {status_code} {request.path}{cors_info}")
        print("-"*80 + "\n")
        
        logger.info(f"响应: {request.method} {request.path} | 状态码: {status_code}{cors_info}")
    
    # Flask-CORS 会自动处理 CORS 头部
    return response

# 配置 CORS（允许跨域请求）
# 根据配置决定是否允许所有来源
if app.config.get('CORS_ALLOW_ALL_ORIGINS'):
    # 允许所有来源（开发环境）
    print("⚠️  CORS 配置: 允许所有来源访问（仅开发环境）")
    CORS(app, 
         resources={r"/api/*": {
             "origins": "*",
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
             "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
             "supports_credentials": False  # 使用 * 时不能使用 credentials
         }},
         supports_credentials=False)
else:
    # 允许指定的来源
    origins = app.config.get('CORS_ORIGINS', [])
    if isinstance(origins, str):
        origins = [origins]
    
    print("✅ CORS 配置: 允许的来源列表:")
    for origin in origins:
        print(f"   - {origin}")
    
    CORS(app,
         resources={r"/api/*": {
             "origins": origins,
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
             "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
             "supports_credentials": app.config.get('CORS_SUPPORTS_CREDENTIALS', True)
         }},
         supports_credentials=app.config.get('CORS_SUPPORTS_CREDENTIALS', True),
         expose_headers=["Content-Type", "Authorization"])  # 暴露的响应头

# OPTIONS 预检请求由 Flask-CORS 自动处理

# 初始化数据库
db.init_app(app)

# 初始化邮箱服务
init_mail(app)

# 初始化认证中间件
init_auth_middleware(app)

# 注册路由模块
register_auth_route(app)  # 注册认证相关路由（/api/register, /api/login, /api/refresh-token, /api/logout）
register_email_routes(app)  # 注册邮箱相关路由（/api/send-verification-code, /api/verify-code）
register_user_routes(app)  # 注册用户相关路由（/api/users/<id>）
register_question_routes(app)  # 注册题目相关路由（/api/questions, /api/questions/<id>, /api/questions/batch, /api/questions/statistics）
register_question_dedup_routes(app)  # 注册题目去重相关路由（/api/dedup/*）

# 注册 WebSocket 路由
from src.routes.websocket import register_websocket_routes
register_websocket_routes(socketio)

# 创建数据库表
with app.app_context():
    print("=" * 80)
    print("📊 数据库配置信息")
    print("=" * 80)
    print(f"数据库 URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"数据库引擎: {db.engine}")
    
    try:
        # 显示数据库配置信息
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        db_type = 'MySQL' if 'mysql' in db_uri.lower() else 'SQLite' if 'sqlite' in db_uri.lower() else 'Unknown'
        print(f"数据库类型: {db_type}")
        
        # 测试数据库连接（使用 try-except 确保连接失败不会阻止应用启动）
        try:
            with db.engine.connect() as conn:
                if db_type == 'MySQL':
                    # MySQL 特定查询
                    try:
                        result = conn.execute(db.text("SELECT DATABASE(), USER()"))
                        db_info = result.fetchone()
                        if db_info:
                            print(f"   数据库: {db_info[0]}")
                            print(f"   用户: {db_info[1]}")
                    except Exception:
                        # 如果查询失败，使用简单查询测试连接
                        conn.execute(db.text("SELECT 1"))
                        print(f"   连接: {db_uri.split('@')[1] if '@' in db_uri else 'Unknown'}")
                else:
                    # SQLite 简单查询
                    result = conn.execute(db.text("SELECT 1"))
                    print(f"   数据库文件: {db_uri.split('/')[-1] if '/' in db_uri else db_uri}")
                print("✅ 数据库连接正常")
        except Exception as conn_error:
            print(f"⚠️  数据库连接失败: {str(conn_error)}")
            if 'cryptography' in str(conn_error).lower():
                print("   提示: 请安装 cryptography 包: pip install cryptography")
            elif 'mysql' in db_type.lower():
                print("   提示: 请检查 MySQL 服务是否运行，以及连接信息是否正确")
            print("   应用将继续启动，但数据库功能可能不可用")
        
        # 创建所有表（如果连接成功）
        try:
            db.create_all()
            print("✅ 数据库表检查/创建完成")
        except Exception as create_error:
            print(f"⚠️  创建数据库表失败: {str(create_error)}")
        
        # 显示当前用户数量
        try:
            user_count = User.query.count()
            print(f"📊 当前用户数量: {user_count}")
        except Exception as query_error:
            # 如果查询失败（可能是表结构不匹配），只显示警告
            print(f"⚠️  无法查询用户数量: {str(query_error)}")
            print("   提示: 可能需要更新数据库表结构")
        
        print("=" * 80)
        print()
    except Exception as e:
        print(f"❌ 数据库初始化异常: {str(e)}")
        print("   应用将继续启动，但数据库功能可能不可用")
        import traceback
        traceback.print_exc()
        print("=" * 80)
        print()

@app.route('/')
def index():
    """首页（保留原有功能）"""
    return jsonify({
        'message': 'Flask API 服务',
        'version': '1.0.0',
        'endpoints': {
            'register': '/api/register',
            'send_code': '/api/send-verification-code',
            'verify_code': '/api/verify-code',
            'health': '/api/health'
        }
    })

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'message': '服务运行正常'
    })

# 所有 API 路由已迁移到对应的路由模块：
# - /api/register -> src/routes/auth.py (register_route)
# - /api/send-verification-code -> src/routes/email.py (register_email_routes)
# - /api/verify-code -> src/routes/email.py (register_email_routes)
# - /api/users/<id> -> src/routes/user.py (register_user_routes)

if __name__ == '__main__':
    import socket
    import sys
    
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
    
    # Windows 系统使用 127.0.0.1 而不是 0.0.0.0，避免权限问题
    if sys.platform == 'win32':
        host = '127.0.0.1'
    else:
        host = '0.0.0.0'
    
    if selected_port != default_port:
        print(f"⚠️  端口 {default_port} 被占用，使用端口 {selected_port}")
    
    print(f"📍 服务地址: http://localhost:{selected_port}")
    print(f"📡 API 路径: http://localhost:{selected_port}/api")
    print(f"🔌 WebSocket 地址: ws://localhost:{selected_port}/socket.io/")
    
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
        socketio.run(app, debug=True, host=host, port=selected_port, allow_unsafe_werkzeug=True)
    except OSError as e:
        print(f"\n❌ 启动失败: {str(e)}")
        print("\n💡 解决方案:")
        print("   1. 检查端口是否被其他程序占用")
        print("   2. 尝试以管理员权限运行")
        print("   3. 检查防火墙设置")
        print("   4. 尝试使用其他端口（修改代码中的 ports_to_try 列表）")
        sys.exit(1)
