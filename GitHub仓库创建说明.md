# GitHub 仓库创建说明

## 📋 方式一：使用脚本创建（推荐）

### 步骤 1: 获取 GitHub Personal Access Token

1. 访问：https://github.com/settings/tokens
2. 点击 **"Generate new token"** → **"Generate new token (classic)"**
3. 填写 Token 名称（例如：`创建仓库`）
4. 选择过期时间（建议选择较长时间，如 90 天）
5. **重要**：勾选 `repo` 权限（完整控制私有仓库）
6. 点击 **"Generate token"**
7. **立即复制 Token**（只显示一次！）

### 步骤 2: 运行创建脚本

```bash
python create_github_repo.py
```

然后按提示输入：
- GitHub Token
- 仓库名称（默认：zxxsys_server）
- 仓库描述（可选）
- 是否私有仓库

---

## 📋 方式二：手动创建（如果没有 Token）

### 步骤 1: 在 GitHub 网站创建仓库

1. 访问：https://github.com/new
2. 填写仓库信息：
   - Repository name: `zxxsys_server`
   - Description: `Flask 后端服务 - 包含用户注册、邮箱验证码等功能`
   - 选择 Public 或 Private
   - **不要**勾选 "Add a README file"（本地已有文件）
   - **不要**添加 .gitignore 或 license
3. 点击 **"Create repository"**

### 步骤 2: 连接本地仓库到远程

复制 GitHub 显示的仓库地址，然后运行：

```bash
# HTTPS 方式
git remote add origin https://github.com/你的用户名/zxxsys_server.git

# 或 SSH 方式（如果已配置 SSH 密钥）
git remote add origin git@github.com:你的用户名/zxxsys_server.git

# 推送代码
git push -u origin master
```

---

## ✅ 创建完成后的操作

脚本会自动创建仓库并显示后续命令。如果没有使用脚本，请手动执行：

```bash
# 1. 添加远程仓库
git remote add origin https://github.com/你的用户名/zxxsys_server.git

# 2. 推送代码
git push -u origin master
```

---

## 🔐 Token 权限说明

创建仓库需要以下权限：
- ✅ **repo** - 完整控制私有仓库（包括创建仓库）

---

## ❓ 常见问题

### Q: Token 过期了怎么办？
A: 重新生成新的 Token，然后更新使用该 Token 的工具配置。

### Q: 忘记保存 Token 了？
A: 只能重新生成新的 Token。

### Q: 仓库名称已存在怎么办？
A: 脚本会提示错误，请更换其他仓库名称。

### Q: 推送代码时提示认证失败？
A: 如果使用 HTTPS，GitHub 已经不支持密码认证，需要：
- 使用 Personal Access Token 作为密码
- 或配置 SSH 密钥使用 SSH 方式

