# Flask 后端服务

这是一个基于 Flask 的后端 API 服务，提供邮箱注册功能，支持与 Vue3 + TypeScript 前端项目集成。

## 📁 项目结构

```
zxxsys_server/
├── src/                    # 核心应用代码
│   ├── app.py             # Flask 应用主文件
│   ├── config.py          # 配置管理
│   ├── models.py          # 数据模型
│   └── email_service.py   # 邮箱服务
│
├── scripts/               # 工具脚本
│   ├── database/          # 数据库相关脚本
│   ├── test/              # 测试脚本
│   └── utils/             # 工具脚本
│
├── docs/                  # 文档
│   ├── api/               # API 文档
│   ├── setup/             # 配置说明
│   ├── guides/            # 使用指南
│   └── database/          # 数据库相关文档
│
├── tests/                 # 单元测试（pytest）
├── templates/             # HTML 模板
├── sql/                   # SQL 文件
└── frontend/              # 前端示例代码
```

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `env.example` 为 `.env` 并修改配置：

```env
DB_TYPE=mysql  # 或 sqlite
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_DATABASE=test
```

### 3. 初始化数据库

```bash
python scripts/database/init_db.py
```

### 4. 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

## 📚 文档

- **API 文档**: [docs/api/API.md](docs/api/API.md)
- **前端对接**: [docs/api/前端对接文档.md](docs/api/前端对接文档.md)
- **配置说明**: [docs/setup/](docs/setup/)
- **使用指南**: [docs/guides/](docs/guides/)

## 🧪 测试

运行测试：

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_api.py -v
```

## 📝 主要功能

- ✅ 邮箱注册 API
- ✅ 邮箱验证码发送和验证
- ✅ 密码加密存储（支持 MD5 + scrypt）
- ✅ SQLite/MySQL 数据库支持
- ✅ CORS 跨域支持
- ✅ RESTful API 设计
- ✅ 完整的错误处理和验证

## 🔧 配置

### 数据库配置

项目支持 SQLite 和 MySQL，通过 `DB_TYPE` 环境变量切换：

```env
# MySQL（默认）
DB_TYPE=mysql
MYSQL_USER=root
MYSQL_PASSWORD=123456

# SQLite
DB_TYPE=sqlite
SQLITE_DB_PATH=app.db
```

详细配置说明请查看 [docs/setup/数据库配置说明.md](docs/setup/数据库配置说明.md)

## 📖 更多信息

详细的功能说明和使用指南请查看 `docs/` 目录下的相关文档。
