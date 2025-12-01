from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from config import Config
from models import db, User
from email_service import init_mail, send_verification_code, verify_code

app = Flask(__name__)
app.config.from_object(Config)

# 配置 CORS（允许跨域请求）
CORS(app, resources={
    r"/api/*": {
        "origins": app.config['CORS_ORIGINS'],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 初始化数据库
db.init_app(app)

# 初始化邮箱服务
init_mail(app)

# 创建数据库表
with app.app_context():
    db.create_all()

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
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        verification_code = data.get('verification_code', '').strip()
        
        # 验证邮箱格式
        if not email:
            return jsonify({
                'success': False,
                'message': '邮箱不能为空'
            }), 400
        
        if not re.match(Config.EMAIL_REGEX, email):
            return jsonify({
                'success': False,
                'message': '邮箱格式不正确'
            }), 400
        
        # 验证密码
        if not password:
            return jsonify({
                'success': False,
                'message': '密码不能为空'
            }), 400
        
        if len(password) < Config.MIN_PASSWORD_LENGTH:
            return jsonify({
                'success': False,
                'message': f'密码长度至少为 {Config.MIN_PASSWORD_LENGTH} 位'
            }), 400
        
        # 验证验证码
        if not verification_code:
            return jsonify({
                'success': False,
                'message': '验证码不能为空'
            }), 400
        
        # 检查验证码（包含时效性检查）
        from email_service import verify_code
        verify_result = verify_code(email, verification_code)
        
        if not verify_result.get('success'):
            # verify_code 函数已经检查了验证码的有效性和过期时间
            return jsonify({
                'success': False,
                'message': verify_result.get('message', '验证码验证失败')
            }), 400
        
        # 检查邮箱是否已存在
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': '该邮箱已被注册'
            }), 409
        
        # 创建新用户（默认权限为普通用户）
        new_user = User(
            email=email,
            role=Config.DEFAULT_USER_ROLE
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'data': new_user.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'注册失败: {str(e)}'
        }), 500

@app.route('/api/send-verification-code', methods=['POST'])
def send_code():
    """发送邮箱验证码"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({
                'success': False,
                'message': '邮箱不能为空'
            }), 400
        
        if not re.match(Config.EMAIL_REGEX, email):
            return jsonify({
                'success': False,
                'message': '邮箱格式不正确'
            }), 400
        
        result = send_verification_code(email)
        
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
        return jsonify({
            'success': False,
            'message': f'发送验证码失败: {str(e)}'
        }), 500

@app.route('/api/verify-code', methods=['POST'])
def verify_verification_code():
    """验证邮箱验证码"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        email = data.get('email', '').strip()
        code = data.get('code', '').strip()
        
        if not email or not code:
            return jsonify({
                'success': False,
                'message': '邮箱和验证码不能为空'
            }), 400
        
        result = verify_code(email, code)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
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
    app.run(debug=True, host='0.0.0.0', port=5000)
