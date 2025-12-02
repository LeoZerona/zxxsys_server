"""查看 email_verifications 表的数据"""
from app import app, db
from models import EmailVerification
from datetime import datetime

with app.app_context():
    print("=" * 80)
    print("📧 邮箱验证码表数据")
    print("=" * 80)
    print(f"数据库 URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print()
    
    try:
        # 查询所有验证码记录
        verifications = EmailVerification.query.order_by(EmailVerification.created_at.desc()).all()
        
        print(f"总记录数: {len(verifications)}")
        print()
        
        if verifications:
            print("验证码记录列表:")
            print("-" * 80)
            for i, v in enumerate(verifications, 1):
                # 判断是否过期
                now = datetime.utcnow()
                is_expired = now > v.expires_at
                status = "✅ 有效" if not v.is_used and not is_expired else \
                        "❌ 已使用" if v.is_used else \
                        "⏰ 已过期"
                
                print(f"{i}. 邮箱: {v.email}")
                print(f"   验证码: {v.code}")
                print(f"   状态: {status}")
                print(f"   创建时间: {v.created_at}")
                print(f"   过期时间: {v.expires_at}")
                print(f"   是否已使用: {'是' if v.is_used else '否'}")
                if is_expired:
                    expired_seconds = (now - v.expires_at).total_seconds()
                    expired_hours = expired_seconds / 3600
                    print(f"   过期时长: {expired_hours:.2f} 小时")
                print("-" * 80)
        else:
            print("⚠️  表中没有验证码记录")
            print()
            print("💡 提示:")
            print("   - 如果从未发送过验证码，表中会是空的")
            print("   - 如果使用了万能验证码，也不会在该表中创建记录")
        
        print()
        print("=" * 80)
        
        # 统计信息
        if verifications:
            used_count = sum(1 for v in verifications if v.is_used)
            expired_count = sum(1 for v in verifications if not v.is_used and datetime.utcnow() > v.expires_at)
            active_count = len(verifications) - used_count - expired_count
            
            print("📊 统计信息:")
            print(f"   - 总记录数: {len(verifications)}")
            print(f"   - 已使用: {used_count}")
            print(f"   - 已过期: {expired_count}")
            print(f"   - 有效: {active_count}")
            print("=" * 80)
        
    except Exception as e:
        print(f"❌ 查询数据库时出错: {str(e)}")
        import traceback
        traceback.print_exc()

