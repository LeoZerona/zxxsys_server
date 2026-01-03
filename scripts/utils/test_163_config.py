"""检查邮箱配置（支持所有邮箱服务商）"""
from src.app import app

print("=" * 60)
print("邮箱配置检查")
print("=" * 60)
print(f"邮箱服务器: {app.config.get('MAIL_SERVER')}")
print(f"邮箱端口: {app.config.get('MAIL_PORT')}")
print(f"使用 SSL: {app.config.get('MAIL_USE_SSL')}")
print(f"使用 TLS: {app.config.get('MAIL_USE_TLS')}")
print(f"邮箱用户名: {app.config.get('MAIL_USERNAME')}")
password = app.config.get('MAIL_PASSWORD')
print(f"是否配置密码: {'是 (已隐藏)' if password else '否'}")
print(f"发送者邮箱: {app.config.get('MAIL_DEFAULT_SENDER')}")
print("=" * 60)

# 判断邮箱服务商
mail_server = app.config.get('MAIL_SERVER', '').lower()
mail_username = app.config.get('MAIL_USERNAME', '')

if app.config.get('MAIL_USERNAME') and app.config.get('MAIL_PASSWORD'):
    # 识别邮箱服务商
    if '163.com' in mail_server or '163.com' in mail_username:
        email_provider = "163 邮箱"
    elif '126.com' in mail_server or '126.com' in mail_username:
        email_provider = "126 邮箱"
    elif 'qq.com' in mail_server or 'qq.com' in mail_username:
        email_provider = "QQ 邮箱"
    elif 'gmail.com' in mail_server or 'gmail.com' in mail_username:
        email_provider = "Gmail"
    elif 'outlook.com' in mail_server or 'outlook.com' in mail_username or 'hotmail.com' in mail_username:
        email_provider = "Outlook/Hotmail"
    else:
        email_provider = "自定义邮箱"
    
    print(f"✓ {email_provider} 配置已设置，将发送真实邮件")
else:
    print("⚠ 邮箱配置未完整，将使用测试模式")
    print("\n提示:")
    print("1. 请检查 .env 文件")
    print("2. 配置 MAIL_USERNAME 和 MAIL_PASSWORD")
    print("3. 大部分邮箱需要使用授权码，不是登录密码")
    print("4. 查看 '邮箱配置说明-多邮箱.md' 了解详细配置方法")

