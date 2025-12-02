from flask import Flask, request, jsonify
from flask_cors import CORS
import re
import logging
from datetime import datetime
from src.config import Config
from src.models import db, User
from src.email_service import init_mail, send_verification_code, verify_code

app = Flask(__name__)
app.config.from_object(Config)

# 配置日志
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
        
        # 测试数据库连接
        with db.engine.connect() as conn:
            if db_type == 'MySQL':
                # MySQL 特定查询
                result = conn.execute(db.text("SELECT DATABASE(), USER()"))
                db_info = result.fetchone()
                if db_info:
                    print(f"   数据库: {db_info[0]}")
                    print(f"   用户: {db_info[1]}")
            else:
                # SQLite 简单查询
                result = conn.execute(db.text("SELECT 1"))
                print(f"   数据库文件: {db_uri.split('/')[-1] if '/' in db_uri else db_uri}")
            print("✅ 数据库连接正常")
        
        # 创建所有表
        db.create_all()
        print("✅ 数据库表检查/创建完成")
        
        # 显示当前用户数量
        user_count = User.query.count()
        print(f"📊 当前用户数量: {user_count}")
        print("=" * 80)
        print()
    except Exception as e:
        print(f"❌ 数据库初始化失败: {str(e)}")
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

@app.route('/api/register', methods=['POST'])
def register():
    """邮箱注册接口"""
    try:
        # 获取请求数据
        data = request.get_json()
        
        print("👤 用户注册接口被调用")
        if data:
            email = data.get('email', '').strip()
            print(f"   邮箱: {email}")
            print(f"   验证码: {'已提供' if data.get('verification_code') else '未提供'}")
            print(f"   密码: {'已提供' if data.get('password') else '未提供'}")
        
        if not data:
            print("   ⚠️ 错误: 请求数据为空")
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        verification_code = data.get('verification_code', '').strip()
        
        # 验证邮箱格式
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
        
        print(f"   ✅ 邮箱格式验证通过")
        
        # 验证密码
        if not password:
            print("   ⚠️ 错误: 密码为空")
            return jsonify({
                'success': False,
                'message': '密码不能为空'
            }), 400
        
        # 检查是否是 MD5 哈希值（前端已加密）
        from models import User
        is_md5 = User.is_md5_hash(password)
        
        if is_md5:
            print(f"   🔐 检测到前端传入的是 MD5 加密密码（32位）")
            # MD5 值长度固定为 32 位，无需验证长度
        else:
            # 明文密码需要验证长度
            if len(password) < Config.MIN_PASSWORD_LENGTH:
                print(f"   ⚠️ 错误: 密码长度不足 (当前: {len(password)}, 需要: {Config.MIN_PASSWORD_LENGTH})")
                return jsonify({
                    'success': False,
                    'message': f'密码长度至少为 {Config.MIN_PASSWORD_LENGTH} 位'
                }), 400
        
        print(f"   ✅ 密码验证通过")
        
        # 验证验证码
        if not verification_code:
            print("   ⚠️ 错误: 验证码为空")
            return jsonify({
                'success': False,
                'message': '验证码不能为空'
            }), 400
        
        print(f"   🔍 开始验证验证码...")
        # 检查验证码（包含时效性检查）
        from email_service import verify_code
        verify_result = verify_code(email, verification_code)
        
        if not verify_result.get('success'):
            print(f"   ❌ 验证码验证失败: {verify_result.get('message', '未知错误')}")
            # verify_code 函数已经检查了验证码的有效性和过期时间
            return jsonify({
                'success': False,
                'message': verify_result.get('message', '验证码验证失败')
            }), 400
        
        print(f"   ✅ 验证码验证通过")
        
        # 检查邮箱是否已存在
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"   ⚠️ 错误: 邮箱已被注册")
            return jsonify({
                'success': False,
                'message': '该邮箱已被注册'
            }), 409
        
        print(f"   📝 开始创建用户...")
        # 创建新用户（默认权限为普通用户）
        new_user = User(
            email=email,
            role=Config.DEFAULT_USER_ROLE
        )
        new_user.set_password(password)
        
        print(f"   🔍 准备添加到数据库会话...")
        db.session.add(new_user)
        
        # 刷新会话，确保对象已附加
        db.session.flush()
        print(f"   🔍 用户对象已添加到会话，临时ID: {new_user.id if hasattr(new_user, 'id') and new_user.id else '未生成'}")
        
        print(f"   🔍 开始提交事务...")
        try:
            db.session.commit()
            print(f"   ✅ 数据库提交成功!")
        except Exception as commit_error:
            print(f"   ❌ 数据库提交失败: {str(commit_error)}")
            db.session.rollback()
            raise commit_error
        
        # 刷新会话，确保获取到最新的ID
        db.session.refresh(new_user)
        
        # 验证用户是否真的保存到数据库（使用新会话查询）
        print(f"   🔍 验证用户是否保存到数据库...")
        # 创建一个新的查询来验证
        saved_user = User.query.filter_by(email=email).first()
        if saved_user:
            print(f"   ✅ 用户已成功保存到数据库! 用户ID: {saved_user.id}, 邮箱: {saved_user.email}, 角色: {saved_user.role}")
            print(f"   📊 数据库 URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
        else:
            print(f"   ⚠️  警告: 用户提交成功但无法从数据库查询到!")
            print(f"   📊 数据库 URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
            print(f"   💡 提示: 请检查您查询的数据库是否正确")
        
        print(f"   ✅ 用户注册成功! 用户ID: {new_user.id}, 角色: {new_user.role}")
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'data': new_user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"   ❌ 注册过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'注册失败: {str(e)}'
        }), 500

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

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """获取用户信息（示例接口）"""
    user = User.query.get_or_404(user_id)
    return jsonify({
        'success': True,
        'data': user.to_dict()
    })

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 Flask 后端服务启动中...")
    print("="*80)
    print(f"📍 服务地址: http://localhost:5000")
    print(f"📡 API 路径: http://localhost:5000/api")
    
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
    app.run(debug=True, host='0.0.0.0', port=5000)
