# 🚀 快速创建 GitHub 仓库并推送代码

## 方式一：使用脚本自动创建（推荐）

### 1. 获取 GitHub Token

访问：https://github.com/settings/tokens/new

- 名称：`创建仓库`
- 过期时间：90天（或更长）
- **勾选 `repo` 权限**
- 点击 "Generate token"
- **复制 Token**（只显示一次！）

### 2. 运行脚本

```bash
python create_github_repo.py
```

按提示输入：
- Token
- 仓库名称（默认：zxxsys_server）
- 描述（直接回车用默认）
- 是否私有（y/N）

### 3. 脚本会自动执行后续操作

---

## 方式二：手动创建（更简单）

### 1. 在 GitHub 网站创建仓库

访问：https://github.com/new

填写：
- Repository name: `zxxsys_server`
- Description: `Flask 后端服务 - 包含用户注册、邮箱验证码等功能`
- Public 或 Private（按需选择）
- **不要勾选任何初始化选项**

点击 **"Create repository"**

### 2. 复制仓库地址

创建后，GitHub 会显示仓库地址，类似：
```
https://github.com/你的用户名/zxxsys_server.git
```

### 3. 连接并推送

告诉我你的仓库地址，我会帮你执行：
```bash
git remote add origin 你的仓库地址
git push -u origin master
```

---

## ✅ 选择哪种方式？

- **方式一**：自动化，但需要 Token
- **方式二**：更简单，直接在网站创建，然后告诉我地址即可

