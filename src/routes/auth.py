"""
认证相关路由（注册、登录等）
"""
from flask import request, jsonify, g
import re
from datetime import datetime, timedelta
from src.models import db, User, RefreshToken, LoginAttempt
from src.config import Config
from src.services.email_service import verify_code
from src.services.captcha_service import CaptchaService
from src.services.permission_service import PermissionService
from src.utils.jwt_utils import JWTUtils
from src.middleware.auth_middleware import hash_token


def register_route(app):
    """注册认证相关的路由"""
    
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
            
            # 获取并清理输入数据（防止SQL注入和XSS）
            email = data.get('email', '').strip()
            password = data.get('password', '').strip()
            verification_code = data.get('verification_code', '').strip()
            
            # 输入长度限制检查（防止过长的输入导致问题）
            if len(email) > 120:
                return jsonify({
                    'success': False,
                    'message': '邮箱长度超出限制'
                }), 400
            
            if len(password) > 500:  # 允许较长的密码（包括MD5哈希）
                return jsonify({
                    'success': False,
                    'message': '密码长度超出限制'
                }), 400
            
            if len(verification_code) > 10:
                return jsonify({
                    'success': False,
                    'message': '验证码格式不正确'
                }), 400
            
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
            verify_result = verify_code(email, verification_code)
            
            if not verify_result.get('success'):
                print(f"   ❌ 验证码验证失败: {verify_result.get('message', '未知错误')}")
                # verify_code 函数已经检查了验证码的有效性和过期时间
                return jsonify({
                    'success': False,
                    'message': verify_result.get('message', '验证码验证失败')
                }), 400
            
            print(f"   ✅ 验证码验证通过")
            
            # 检查邮箱是否已存在（使用参数化查询，防止SQL注入）
            # SQLAlchemy 的 filter_by 使用参数化查询，自动防止 SQL 注入
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

    @app.route('/api/login', methods=['POST'])
    def login():
        """用户登录接口（支持登录失败次数限制和验证码验证）"""
        try:
            data = request.get_json()
            
            print("🔐 用户登录接口被调用")
            
            if not data:
                print("   ⚠️ 错误: 请求数据为空")
                return jsonify({
                    'success': False,
                    'message': '请求数据不能为空'
                }), 400
            
            email = data.get('email', '').strip()
            password = data.get('password', '').strip()
            captcha_session_key = data.get('captcha_session_key', '').strip()  # 验证码会话键
            captcha_code = data.get('captcha_code', '').strip()  # 用户输入的验证码
            
            if not email:
                print("   ⚠️ 错误: 邮箱为空")
                return jsonify({
                    'success': False,
                    'message': '邮箱不能为空'
                }), 400
            
            if not password:
                print("   ⚠️ 错误: 密码为空")
                return jsonify({
                    'success': False,
                    'message': '密码不能为空'
                }), 400
            
            # 验证邮箱格式
            if not re.match(Config.EMAIL_REGEX, email):
                print(f"   ⚠️ 错误: 邮箱格式不正确 - {email}")
                return jsonify({
                    'success': False,
                    'message': '邮箱格式不正确'
                }), 400
            
            # 获取IP地址
            ip_address = request.remote_addr
            
            # 检查登录失败记录
            login_attempt = LoginAttempt.query.filter_by(email=email).first()
            now = datetime.utcnow()
            requires_captcha = False
            
            if login_attempt:
                # 检查时间窗口是否过期（超过10分钟）
                time_diff = now - login_attempt.first_attempt_at
                if time_diff > timedelta(minutes=Config.LOGIN_FAIL_WINDOW_MINUTES):
                    # 时间窗口已过，重置记录
                    print(f"   🔄 登录失败记录已过期，重置记录")
                    login_attempt.reset()
                    login_attempt.first_attempt_at = now
                    login_attempt.last_attempt_at = now
                    login_attempt.ip_address = ip_address
                    db.session.commit()
                else:
                    # 检查是否需要验证码（失败次数 >= 10次）
                    if login_attempt.attempt_count >= Config.LOGIN_FAIL_LIMIT:
                        requires_captcha = True
                        login_attempt.requires_captcha = True
                        print(f"   🔐 登录失败次数已达限制，需要验证码 (失败次数: {login_attempt.attempt_count})")
            
            # 如果需要验证码，验证验证码
            if requires_captcha:
                if not captcha_session_key or not captcha_code:
                    print(f"   ⚠️ 需要验证码但未提供")
                    db.session.commit()
                    return jsonify({
                        'success': False,
                        'message': f'登录失败次数过多，请输入验证码',
                        'code': 'REQUIRES_CAPTCHA',
                        'requires_captcha': True
                    }), 400
                
                # 验证验证码
                captcha_result = CaptchaService.verify_captcha(captcha_session_key, captcha_code)
                if not captcha_result['success']:
                    print(f"   ⚠️ 验证码验证失败: {captcha_result['message']}")
                    # 验证码错误也算一次失败
                    if login_attempt:
                        login_attempt.attempt_count += 1
                        login_attempt.last_attempt_at = now
                        db.session.commit()
                    return jsonify({
                        'success': False,
                        'message': captcha_result['message'],
                        'code': 'INVALID_CAPTCHA',
                        'requires_captcha': True
                    }), 400
                
                print(f"   ✅ 验证码验证通过")
                login_attempt.captcha_verified = True
            
            # 查询用户
            user = User.query.filter_by(email=email).first()
            
            # 记录登录失败（在验证之前先记录，无论用户是否存在）
            login_failed = False
            if not user:
                print(f"   ⚠️ 错误: 用户不存在 - {email}")
                login_failed = True
            elif not user.check_password(password):
                print(f"   ⚠️ 错误: 密码错误 - {email}")
                login_failed = True
            elif not user.is_active:
                print(f"   ⚠️ 错误: 账户已被禁用 - {email}")
                return jsonify({
                    'success': False,
                    'message': '账户已被禁用，请联系管理员',
                    'code': 'USER_BANNED'
                }), 403
            
            # 如果登录失败，记录失败次数
            if login_failed:
                if not login_attempt:
                    # 创建新的失败记录
                    login_attempt = LoginAttempt(
                        email=email,
                        ip_address=ip_address,
                        attempt_count=1,
                        first_attempt_at=now,
                        last_attempt_at=now
                    )
                    db.session.add(login_attempt)
                else:
                    # 更新失败次数
                    login_attempt.attempt_count += 1
                    login_attempt.last_attempt_at = now
                    login_attempt.ip_address = ip_address
                    
                    # 如果达到限制次数，设置需要验证码
                    if login_attempt.attempt_count >= Config.LOGIN_FAIL_LIMIT:
                        login_attempt.requires_captcha = True
                        requires_captcha = True
                
                db.session.commit()
                
                # 返回错误（为了安全，不透露用户是否存在）
                response_data = {
                    'success': False,
                    'message': '邮箱或密码错误'
                }
                
                # 如果需要验证码，返回提示
                if requires_captcha:
                    response_data['code'] = 'REQUIRES_CAPTCHA'
                    response_data['requires_captcha'] = True
                    response_data['message'] = f'登录失败次数过多，请输入验证码'
                    response_data['attempt_count'] = login_attempt.attempt_count
                
                return jsonify(response_data), 401
            
            # 登录成功，清除失败记录
            if login_attempt:
                print(f"   ✅ 登录成功，清除失败记录")
                db.session.delete(login_attempt)
                db.session.commit()
            
            print(f"   ✅ 用户验证成功: {email}")
            
            # 生成 Token
            access_token = JWTUtils.generate_access_token(
                user_id=user.id,
                email=user.email,
                role=user.role
            )
            
            refresh_token = JWTUtils.generate_refresh_token(user_id=user.id)
            
            # 可选：将 Refresh Token 存储到数据库（用于服务端管理）
            # 获取客户端信息
            user_agent = request.headers.get('User-Agent', '')
            ip_address = request.remote_addr
            
            # 存储 Refresh Token 到数据库
            refresh_token_hash = hash_token(refresh_token)
            
            # 检查是否已存在该用户的 Refresh Token（可选：限制每个用户的 Refresh Token 数量）
            existing_token = RefreshToken.query.filter_by(
                user_id=user.id,
                token_hash=refresh_token_hash
            ).first()
            
            if not existing_token:
                # 创建新的 Refresh Token 记录
                refresh_token_record = RefreshToken(
                    user_id=user.id,
                    token_hash=refresh_token_hash,
                    expires_at=datetime.utcnow() + timedelta(seconds=JWTUtils.REFRESH_TOKEN_EXPIRE),
                    user_agent=user_agent[:255],  # 限制长度
                    ip_address=ip_address
                )
                db.session.add(refresh_token_record)
                db.session.commit()
            
            print(f"   ✅ Token 生成成功")
            
            # 获取用户权限信息（菜单和操作权限）
            permission_info = PermissionService.get_user_permission_info(user.role)
            print(f"   📋 用户角色: {user.role}, 权限数量: {len(permission_info['permissions'])}, 菜单数量: {len(permission_info['menus'])}")
            
            # 返回用户信息和 Token
            return jsonify({
                'success': True,
                'message': '登录成功',
                'data': {
                    'user': user.to_dict(),
                    'role': user.role,  # 用户角色信息
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'token_type': 'Bearer',
                    'expires_in': JWTUtils.ACCESS_TOKEN_EXPIRE,  # 秒
                    'permissions': permission_info['permissions'],  # 用户拥有的所有操作权限
                    'menus': permission_info['menus']  # 用户可访问的菜单列表
                }
            }), 200
        
        except Exception as e:
            db.session.rollback()
            print(f"   ❌ 登录过程中发生异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'登录失败: {str(e)}'
            }), 500

    @app.route('/api/captcha', methods=['GET'])
    def get_captcha():
        """获取验证码接口"""
        try:
            print("🖼️ 获取验证码接口被调用")
            
            # 生成验证码
            captcha_result = CaptchaService.generate_captcha()
            
            return jsonify({
                'success': True,
                'message': '验证码生成成功',
                'data': {
                    'captcha_code': captcha_result['captcha_code'],
                    'session_key': captcha_result['session_key'],
                    'expires_in': captcha_result['expires_in']
                }
            }), 200
        
        except Exception as e:
            print(f"   ❌ 生成验证码过程中发生异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'生成验证码失败: {str(e)}'
            }), 500

    @app.route('/api/refresh-token', methods=['POST'])
    def refresh_token():
        """刷新 Token 接口"""
        try:
            data = request.get_json()
            
            print("🔄 刷新 Token 接口被调用")
            
            if not data:
                return jsonify({
                    'success': False,
                    'message': '请求数据不能为空'
                }), 400
            
            refresh_token = data.get('refresh_token', '').strip()
            
            if not refresh_token:
                return jsonify({
                    'success': False,
                    'message': 'Refresh Token 不能为空'
                }), 400
            
            # 验证 Refresh Token
            verify_result = JWTUtils.verify_token(refresh_token, token_type='refresh')
            
            if not verify_result['success']:
                print(f"   ⚠️ Refresh Token 验证失败: {verify_result['message']}")
                return jsonify({
                    'success': False,
                    'message': verify_result['message'],
                    'code': 'INVALID_REFRESH_TOKEN'
                }), 401
            
            payload = verify_result['payload']
            user_id = payload.get('user_id')
            
            # 查询用户
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': '用户不存在',
                    'code': 'USER_NOT_FOUND'
                }), 401
            
            # 检查用户状态
            if not user.is_active:
                return jsonify({
                    'success': False,
                    'message': '账户已被禁用，请联系管理员',
                    'code': 'USER_BANNED'
                }), 403
            
            # 可选：验证 Refresh Token 是否在数据库中（如果实现了服务端管理）
            refresh_token_hash = hash_token(refresh_token)
            token_record = RefreshToken.query.filter_by(
                user_id=user.id,
                token_hash=refresh_token_hash
            ).first()
            
            if token_record:
                # 检查 Token 是否已被撤销
                if token_record.is_revoked:
                    return jsonify({
                        'success': False,
                        'message': 'Refresh Token 已被撤销',
                        'code': 'TOKEN_REVOKED'
                    }), 401
                
                # 检查 Token 是否过期（数据库中的过期时间）
                if token_record.is_expired():
                    return jsonify({
                        'success': False,
                        'message': 'Refresh Token 已过期',
                        'code': 'TOKEN_EXPIRED'
                    }), 401
                
                # 更新最后使用时间
                token_record.last_used_at = datetime.utcnow()
                db.session.commit()
            
            # 生成新的 Access Token
            new_access_token = JWTUtils.generate_access_token(
                user_id=user.id,
                email=user.email,
                role=user.role
            )
            
            print(f"   ✅ Token 刷新成功: {user.email}")
            
            return jsonify({
                'success': True,
                'message': 'Token 刷新成功',
                'data': {
                    'access_token': new_access_token,
                    'token_type': 'Bearer',
                    'expires_in': JWTUtils.ACCESS_TOKEN_EXPIRE
                }
            }), 200
        
        except Exception as e:
            db.session.rollback()
            print(f"   ❌ 刷新 Token 过程中发生异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'message': f'刷新 Token 失败: {str(e)}'
            }), 500

    @app.route('/api/logout', methods=['POST'])
    def logout():
        """用户登出接口（可选：撤销 Refresh Token）"""
        try:
            # 需要登录验证
            if not hasattr(g, 'current_user'):
                return jsonify({
                    'success': False,
                    'message': '未登录'
                }), 401
            
            user = g.current_user
            data = request.get_json() or {}
            refresh_token = data.get('refresh_token', '').strip()
            
            # 如果提供了 Refresh Token，撤销它
            if refresh_token:
                refresh_token_hash = hash_token(refresh_token)
                token_record = RefreshToken.query.filter_by(
                    user_id=user.id,
                    token_hash=refresh_token_hash
                ).first()
                
                if token_record:
                    token_record.is_revoked = True
                    db.session.commit()
                    print(f"   ✅ Refresh Token 已撤销: {user.email}")
            
            return jsonify({
                'success': True,
                'message': '登出成功'
            }), 200
        
        except Exception as e:
            db.session.rollback()
            print(f"   ❌ 登出过程中发生异常: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'登出失败: {str(e)}'
            }), 500

