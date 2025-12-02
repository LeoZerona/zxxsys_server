"""邮箱服务模块"""
import random
import string
from datetime import datetime, timedelta
from flask import current_app
from flask_mail import Mail, Message
from src.models import db, EmailVerification

mail = Mail()

def init_mail(app):
    """初始化邮箱服务"""
    mail.init_app(app)

def generate_verification_code(length=6):
    """生成验证码"""
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(email, code):
    """发送验证码邮件"""
    try:
        app = current_app._get_current_object()
        
        # 如果未配置邮箱，则只打印到控制台（用于测试）
        if not app.config.get('MAIL_USERNAME') or not app.config.get('MAIL_PASSWORD'):
            print(f"[测试模式] 发送验证码到 {email}: {code}")
            return True
        
        subject = "再学习教育 - 邮箱验证码"
        
        # 纯文本版本
        body = f"""尊敬的用户，您好！

感谢您选择再学习教育平台！

您的邮箱验证码是：{code}

验证码有效期为 10 分钟，请勿泄露给他人。

如非本人操作，请忽略此邮件。

此邮件由系统自动发送，请勿直接回复。

--
再学习教育
专业成人自考教育平台
为您提供优质的学历提升服务
        """
        
        # HTML 商务风格模板
        html_body = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>邮箱验证码</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Microsoft YaHei', '微软雅黑', Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f5f5f5; padding: 40px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" border="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); max-width: 600px;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 40px 30px; text-align: center; border-radius: 8px 8px 0 0;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: 600; letter-spacing: 1px;">再学习教育</h1>
                            <p style="margin: 10px 0 0; color: #f0f0f0; font-size: 14px;">专业成人自考教育平台</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 20px; color: #333333; font-size: 16px; line-height: 1.6;">尊敬的用户，您好！</p>
                            
                            <p style="margin: 0 0 30px; color: #666666; font-size: 15px; line-height: 1.8;">
                                感谢您选择<span style="color: #667eea; font-weight: 600;">再学习教育</span>平台！我们致力于为您提供优质的成人自考教育服务，助力您的学历提升之路。
                            </p>
                            
                            <div style="background-color: #f8f9fa; border-left: 4px solid #667eea; padding: 25px; margin: 30px 0; border-radius: 4px;">
                                <p style="margin: 0 0 15px; color: #333333; font-size: 14px; font-weight: 600;">您的邮箱验证码：</p>
                                <div style="text-align: center; margin: 20px 0;">
                                    <span style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; font-size: 32px; font-weight: bold; padding: 15px 40px; border-radius: 6px; letter-spacing: 8px; font-family: 'Courier New', monospace;">{code}</span>
                                </div>
                                <p style="margin: 15px 0 0; color: #999999; font-size: 12px; text-align: center;">验证码有效期为 10 分钟</p>
                            </div>
                            
                            <div style="background-color: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; padding: 15px; margin: 25px 0;">
                                <p style="margin: 0; color: #856404; font-size: 13px; line-height: 1.6;">
                                    <strong>安全提示：</strong>为了保障您的账户安全，请勿将验证码泄露给他人。如非本人操作，请立即忽略此邮件。
                                </p>
                            </div>
                            
                            <p style="margin: 30px 0 0; color: #666666; font-size: 14px; line-height: 1.8;">
                                如有任何疑问，欢迎联系我们的客服团队，我们将竭诚为您服务。
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 30px 40px; text-align: center; border-radius: 0 0 8px 8px; border-top: 1px solid #e9ecef;">
                            <p style="margin: 0 0 10px; color: #999999; font-size: 12px;">
                                此邮件由<span style="color: #667eea;">再学习教育</span>系统自动发送，请勿直接回复
                            </p>
                            <p style="margin: 0; color: #cccccc; font-size: 11px;">
                                © {datetime.now().year} 再学习教育 版权所有 | 专业成人自考教育平台
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """
        
        msg = Message(
            subject=subject,
            recipients=[email],
            body=body,
            html=html_body,
            sender=app.config.get('MAIL_DEFAULT_SENDER')
        )
        
        mail.send(msg)
        return True
    
    except Exception as e:
        print(f"发送邮件失败: {str(e)}")
        return False

def send_verification_code(email):
    """生成并发送验证码"""
    try:
        # 检查发送频率限制（1分钟内只能发送一次）
        cooldown_minutes = current_app.config.get('VERIFICATION_CODE_COOLDOWN_MINUTES', 1)
        cooldown_seconds = cooldown_minutes * 60
        
        existing_verification = EmailVerification.query.filter_by(email=email).order_by(
            EmailVerification.created_at.desc()
        ).first()
        
        if existing_verification:
            # 计算距离上次发送的时间
            time_since_last = (datetime.utcnow() - existing_verification.created_at).total_seconds()
            
            if time_since_last < cooldown_seconds:
                # 计算剩余等待时间
                remaining_seconds = int(cooldown_seconds - time_since_last)
                remaining_minutes = remaining_seconds // 60
                remaining_secs = remaining_seconds % 60
                
                if remaining_minutes > 0:
                    wait_time = f"{remaining_minutes}分{remaining_secs}秒"
                else:
                    wait_time = f"{remaining_secs}秒"
                
                return {
                    'success': False,
                    'message': f'发送验证码过于频繁，请等待 {wait_time} 后再试',
                    'cooldown_seconds': remaining_seconds
                }
        
        # 生成验证码
        code = generate_verification_code(
            current_app.config.get('VERIFICATION_CODE_LENGTH', 6)
        )
        
        # 计算过期时间
        expire_minutes = current_app.config.get('VERIFICATION_CODE_EXPIRE_MINUTES', 10)
        expires_at = datetime.utcnow() + timedelta(minutes=expire_minutes)
        
        # 保存或更新验证码到数据库
        print(f"   💾 准备保存验证码到数据库...")
        if existing_verification:
            # 更新现有验证码
            print(f"   🔄 更新现有验证码记录 (ID: {existing_verification.id})")
            existing_verification.code = code
            existing_verification.expires_at = expires_at
            existing_verification.is_used = False
            existing_verification.created_at = datetime.utcnow()
            verification = existing_verification  # 保存引用用于后续验证
        else:
            # 创建新验证码记录
            print(f"   ➕ 创建新的验证码记录")
            verification = EmailVerification(
                email=email,
                code=code,
                expires_at=expires_at
            )
            db.session.add(verification)
            print(f"   ✅ 验证码对象已添加到会话")
        
        # 刷新会话以获取 ID
        db.session.flush()
        print(f"   🔍 验证码记录 ID: {verification.id if verification.id else '未生成'}")
        
        # 提交到数据库
        print(f"   💾 开始提交事务...")
        try:
            db.session.commit()
            print(f"   ✅ 验证码已成功保存到数据库!")
        except Exception as commit_error:
            print(f"   ❌ 数据库提交失败: {str(commit_error)}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            raise commit_error
        
        # 验证验证码是否真的保存到数据库
        print(f"   🔍 验证验证码是否保存成功...")
        saved_verification = EmailVerification.query.filter_by(
            email=email,
            code=code
        ).first()
        
        if saved_verification:
            print(f"   ✅ 验证码已确认保存! ID: {saved_verification.id}, 邮箱: {saved_verification.email}, 验证码: {saved_verification.code}")
        else:
            print(f"   ⚠️  警告: 提交成功但无法从数据库查询到验证码!")
            print(f"   📊 数据库 URI: {current_app.config.get('SQLALCHEMY_DATABASE_URI', '未知')}")
        
        # 发送邮件
        print(f"   📧 准备发送验证码邮件...")
        send_success = send_verification_email(email, code)
        
        if send_success:
            return {
                'success': True,
                'message': '验证码已发送',
                'code': code  # 开发环境可以返回，生产环境应移除
            }
        else:
            return {
                'success': False,
                'message': '发送验证码失败，请稍后重试'
            }
    
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'message': f'发送验证码失败: {str(e)}'
        }

def verify_code(email, code):
    """验证验证码"""
    try:
        # 检查是否是万能验证码（仅开发环境）
        universal_code = current_app.config.get('UNIVERSAL_VERIFICATION_CODE', '')
        if universal_code and code == universal_code:
            print(f"   🔓 使用万能验证码验证成功: {code}")
            print(f"   ⚠️  注意: 这是测试用的万能验证码，生产环境请禁用！")
            return {
                'success': True,
                'message': '验证码验证成功（万能验证码）'
            }
        
        # 正常验证码验证流程
        verification = EmailVerification.query.filter_by(
            email=email,
            code=code,
            is_used=False
        ).first()
        
        if not verification:
            return {
                'success': False,
                'message': '验证码无效'
            }
        
        # 检查是否过期
        if datetime.utcnow() > verification.expires_at:
            return {
                'success': False,
                'message': '验证码已过期，请重新获取'
            }
        
        # 标记为已使用
        verification.is_used = True
        db.session.commit()
        
        return {
            'success': True,
            'message': '验证码验证成功'
        }
    
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'message': f'验证失败: {str(e)}'
        }

