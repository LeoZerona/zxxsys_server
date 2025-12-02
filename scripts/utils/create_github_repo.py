"""
GitHub 仓库创建脚本
使用 GitHub API 创建远程仓库
"""
import requests
import json
import sys

def create_github_repo(token, repo_name, description="Flask 后端服务 - 包含用户注册、邮箱验证码等功能", private=False):
    """
    使用 GitHub API 创建仓库
    
    Args:
        token: GitHub Personal Access Token
        repo_name: 仓库名称
        description: 仓库描述
        private: 是否为私有仓库
    """
    url = "https://api.github.com/user/repos"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "name": repo_name,
        "description": description,
        "private": private,
        "auto_init": False  # 不初始化 README，因为本地已有文件
    }
    
    try:
        print(f"正在创建 GitHub 仓库: {repo_name}...")
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 201:
            repo_info = response.json()
            repo_url = repo_info["clone_url"]
            print(f"✅ 仓库创建成功！")
            print(f"   仓库地址: {repo_url}")
            print(f"   SSH 地址: {repo_info['ssh_url']}")
            return repo_url
        elif response.status_code == 401:
            print("❌ 认证失败，请检查 Token 是否正确")
            sys.exit(1)
        elif response.status_code == 422:
            error_data = response.json()
            if "name" in error_data.get("errors", [{}])[0].get("message", ""):
                print(f"❌ 仓库名称 '{repo_name}' 已存在或格式不正确")
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

if __name__ == "__main__":
    print("=" * 60)
    print("GitHub 仓库创建工具")
    print("=" * 60)
    print()
    print("需要 GitHub Personal Access Token")
    print("如果没有，请访问: https://github.com/settings/tokens")
    print("需要勾选 'repo' 权限")
    print()
    print("=" * 60)
    print()
    
    # 从命令行参数或输入获取 token
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        token = input("请输入你的 GitHub Personal Access Token: ").strip()
    
    if not token:
        print("❌ Token 不能为空")
        sys.exit(1)
    
    # 仓库名称
    repo_name = input("请输入仓库名称 (默认: zxxsys_server): ").strip() or "zxxsys_server"
    
    # 仓库描述
    description = input("请输入仓库描述 (直接回车使用默认描述): ").strip()
    if not description:
        description = "Flask 后端服务 - 包含用户注册、邮箱验证码等功能"
    
    # 是否私有
    is_private = input("是否为私有仓库? (y/N): ").strip().lower() == 'y'
    
    print()
    repo_url = create_github_repo(token, repo_name, description, is_private)
    
    print()
    print("=" * 60)
    print("正在配置 Git 远程仓库...")
    print("=" * 60)
    
    # 自动执行 git 命令
    import subprocess
    import os
    
    try:
        # 检查是否已有远程仓库
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], 
                              capture_output=True, text=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"⚠️  远程仓库已存在: {result.stdout.strip()}")
            overwrite = input("是否要替换为新的仓库地址? (y/N): ").strip().lower()
            if overwrite == 'y':
                subprocess.run(['git', 'remote', 'set-url', 'origin', repo_url], cwd=os.getcwd())
                print("✅ 已更新远程仓库地址")
            else:
                print("跳过设置远程仓库")
                sys.exit(0)
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
            print(f"🎉 仓库地址: https://github.com/{repo_name.split('/')[-1] if '/' in repo_name else repo_name}")
        else:
            print("⚠️  推送时出现错误:")
            print(push_result.stderr)
            print()
            print("请手动执行:")
            print(f"  git push -u origin master")
            
    except Exception as e:
        print(f"⚠️  执行 Git 命令时出错: {e}")
        print()
        print("请手动执行以下命令:")
        print(f"  git remote add origin {repo_url}")
        print(f"  git push -u origin master")
    
    print("=" * 60)

