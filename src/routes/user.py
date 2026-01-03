"""
用户相关路由（获取用户信息等）
"""
from flask import jsonify, g, request
from src.models import User
from src.utils.jwt_utils import login_required, role_required, permission_required


def register_user_routes(app):
    """注册用户相关的路由"""
    
    @app.route('/api/users/<int:user_id>', methods=['GET'])
    @login_required  # 需要登录
    def get_user(user_id):
        """获取用户信息（需要登录）"""
        # 从 g 对象获取当前登录用户
        current_user = g.current_user
        
        # 只能查看自己的信息，除非是管理员
        if current_user.id != user_id and not current_user.is_admin():
            return jsonify({
                'success': False,
                'message': '无权查看其他用户信息',
                'code': 'PERMISSION_DENIED'
            }), 403
        
        user = User.query.get_or_404(user_id)
        return jsonify({
            'success': True,
            'data': user.to_dict()
        })
    
    @app.route('/api/users/me', methods=['GET'])
    @login_required  # 需要登录
    def get_current_user():
        """获取当前登录用户信息"""
        current_user = g.current_user
        return jsonify({
            'success': True,
            'data': current_user.to_dict()
        })
    
    @app.route('/api/users', methods=['GET'])
    @login_required
    @role_required('admin', 'super_admin')  # 需要管理员权限
    def list_users():
        """获取用户列表（仅管理员）"""
        # 分页参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        # 查询用户
        users = User.query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'users': [user.to_dict() for user in users.items],
                'total': users.total,
                'page': page,
                'per_page': per_page,
                'pages': users.pages
            }
        })

