"""
自动创建 GitHub 仓库并推送代码
使用命令行参数传入 Token 和仓库名
"""
import requests
import subprocess
import sys
import os

def create_github_repo(token, repo_name, description="Flask 后端服务 - 包含用户注册、邮箱验证码等功能", private=False):
    """使用 GitHub API 创建仓库"""
    url = "https://api.github.com/user/repos"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "name": repo_name,
        "description": description,
        "private": private,
        "auto_init": False
    }
    
    try:
        print(f"正在创建 GitHub 仓库: {repo_name}...")
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            repo_info = response.json()
            repo_url = repo_info["clone_url"]
            print(f"✅ 仓库创建成功！")
            print(f"   仓库地址: {repo_url}")
            return repo_url
        elif response.status_code == 401:
            print("❌ 认证失败，请检查 Token 是否正确")
            sys.exit(1)
        elif response.status_code == 422:
            error_data = response.json()
            errors = error_data.get("errors", [])
            if errors and "message" in errors[0]:
                error_msg = errors[0]["message"]
                if "name" in error_msg.lower() or "already exists" in error_msg.lower():
                    print(f"❌ 仓库名称 '{repo_name}' 已存在或格式不正确")
                else:
                    print(f"❌ 创建失败: {error_msg}")
            else:
                print(f"❌ 创建失败: {error_data.get('message', '未知错误')}")
            sys.exit(1)
        else:
            print(f"❌ 创建失败 (状态码: {response.status_code})")
            print(f"   错误信息: {response.text}")
            sys.exit(1)
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 网络错误: {e}")
        sys.exit(1)

def setup_and_push(repo_url, repo_name):
    """配置远程仓库并推送代码"""
    try:
        # 检查是否已有远程仓库
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"⚠️  远程仓库已存在: {result.stdout.strip()}")
            # 自动更新
            subprocess.run(['git', 'remote', 'set-url', 'origin', repo_url], cwd=os.getcwd())
            print("✅ 已更新远程仓库地址")
        else:
            # 添加远程仓库
            subprocess.run(['git', 'remote', 'add', 'origin', repo_url], cwd=os.getcwd())
            print(f"✅ 已添加远程仓库: {repo_url}")
        
        print()
        print("=" * 60)
        print("正在推送代码到 GitHub...")
        print("=" * 60)
        
        # 推送代码
        push_result = subprocess.run(['git', 'push', '-u', 'origin', 'master'], 
                                   cwd=os.getcwd(), capture_output=True, text=True)
        
        if push_result.returncode == 0:
            print("✅ 代码推送成功！")
            print()
            print(f"🎉 仓库地址: https://github.com/{repo_name}")
            return True
        else:
            print("⚠️  推送时出现错误:")
            print(push_result.stderr)
            if "Authentication failed" in push_result.stderr or "fatal: could not read Username" in push_result.stderr:
                print("\n💡 提示: 推送需要使用 Token 进行认证")
                print("   请执行以下命令:")
                print(f"   git remote set-url origin https://{token}@github.com/{repo_name}.git")
                print(f"   git push -u origin master")
            return False
            
    except Exception as e:
        print(f"⚠️  执行 Git 命令时出错: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python auto_create_repo.py <token> [repo_name] [description] [private]")
        sys.exit(1)
    
    token = sys.argv[1]
    repo_name = sys.argv[2] if len(sys.argv) > 2 else "zxxsys_server"
    description = sys.argv[3] if len(sys.argv) > 3 else "Flask 后端服务 - 包含用户注册、邮箱验证码等功能"
    is_private = sys.argv[4].lower() == 'true' if len(sys.argv) > 4 else False
    
    print("=" * 60)
    print("GitHub 仓库自动创建工具")
    print("=" * 60)
    print()
    
    # 创建仓库
    repo_url = create_github_repo(token, repo_name, description, is_private)
    
    print()
    print("=" * 60)
    print("正在配置 Git 远程仓库...")
    print("=" * 60)
    
    # 配置并推送
    success = setup_and_push(repo_url, repo_name)
    
    if not success:
        print()
        print("=" * 60)
        print("手动推送命令:")
        print("=" * 60)
        print(f"git remote add origin {repo_url}")
        print("git push -u origin master")
        print("=" * 60)
    
    print("=" * 60)

