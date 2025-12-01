# 功能实现说明文档

## 实现状态

### ✅ 数据库连接

**实现位置**: 
- `app.py` (第 19-24 行) - 数据库初始化和表创建
- `models.py` - 数据库模型定义
- `config.py` (第 12-17 行) - 数据库配置

**功能说明**:
- 使用 Flask-SQLAlchemy 作为 ORM
- 默认使用 SQLite 数据库（`app.db`）
- 支持通过环境变量配置 PostgreSQL 或 MySQL
- 自动创建数据库表

**测试位置**: `tests/test_database.py`

---

### ✅ 邮箱发送功能

**实现位置**:
- `email_service.py` - 邮箱服务核心模块
- `config.py` (第 29-35 行) - 邮箱服务配置
- `app.py` (第 14 行, 第 21 行, 第 48-93 行) - 邮箱服务集成和 API 接口
- `models.py` (第 40-62 行) - 邮箱验证码模型

**功能说明**:
1. **发送验证码邮件** (`send_verification_code`)
   - 生成 6 位数字验证码
   - 保存验证码到数据库
   - 发送验证码邮件（支持 HTML 格式）
   - 测试模式下不发送真实邮件，仅打印到控制台

2. **验证验证码** (`verify_code`)
   - 验证验证码是否正确
   - 检查验证码是否过期（默认 10 分钟）
   - 检查验证码是否已使用
   - 验证成功后标记为已使用

3. **API 接口**:
   - `POST /api/send-verification-code` - 发送验证码
   - `POST /api/verify-code` - 验证验证码

**邮箱配置** (在 `.env` 文件中):
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

**测试位置**: `tests/test_email_service.py`

---

## 测试单元

### 测试文件结构

```
tests/
├── __init__.py              # 测试包初始化
├── conftest.py              # Pytest 配置和 fixtures
├── test_database.py         # 数据库测试
├── test_email_service.py    # 邮箱服务测试
├── test_api.py             # API 接口测试
└── README.md               # 测试文档
```

### 测试覆盖

1. **数据库测试** (`test_database.py`)
   - ✅ 数据库初始化
   - ✅ 数据库连接
   - ✅ 用户模型 CRUD 操作
   - ✅ 邮箱验证码模型操作
   - ✅ 数据验证（唯一性约束等）

2. **邮箱服务测试** (`test_email_service.py`)
   - ✅ 验证码生成
   - ✅ 发送验证码
   - ✅ 验证码验证
   - ✅ 过期处理
   - ✅ 已使用验证码处理

3. **API 测试** (`test_api.py`)
   - ✅ 健康检查接口
   - ✅ 用户注册接口（成功/失败场景）
   - ✅ 发送验证码接口
   - ✅ 验证验证码接口
   - ✅ 获取用户信息接口

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_database.py
pytest tests/test_email_service.py
pytest tests/test_api.py

# 查看详细输出
pytest -v

# 或使用提供的脚本
python run_tests.py
```

---

## 文件位置索引

### 核心文件

| 文件 | 功能 | 关键内容 |
|------|------|----------|
| `app.py` | Flask 应用主文件 | 路由、CORS、数据库初始化 |
| `models.py` | 数据模型 | User、EmailVerification |
| `config.py` | 配置管理 | 数据库、邮箱、CORS 配置 |
| `email_service.py` | 邮箱服务 | 发送邮件、验证码管理 |

### 测试文件

| 文件 | 测试内容 |
|------|----------|
| `tests/test_database.py` | 数据库连接和模型 |
| `tests/test_email_service.py` | 邮箱服务功能 |
| `tests/test_api.py` | API 接口 |
| `tests/conftest.py` | 测试配置和 fixtures |

### 配置文件

| 文件 | 用途 |
|------|------|
| `requirements.txt` | Python 依赖包 |
| `.env.example` | 环境变量示例 |

---

## API 端点

### 用户注册
- `POST /api/register` - 邮箱注册

### 邮箱验证
- `POST /api/send-verification-code` - 发送验证码
- `POST /api/verify-code` - 验证验证码

### 其他
- `GET /api/health` - 健康检查
- `GET /api/users/{id}` - 获取用户信息

---

## 使用示例

### 1. 发送验证码

```bash
curl -X POST http://localhost:5000/api/send-verification-code \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

### 2. 验证验证码

```bash
curl -X POST http://localhost:5000/api/verify-code \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "code": "123456"}'
```

### 3. 用户注册

```bash
curl -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

---

## 注意事项

1. **邮箱配置**: 如果没有配置邮箱服务，系统会以测试模式运行，验证码会打印到控制台
2. **数据库**: 测试使用临时数据库，生产环境建议使用 PostgreSQL 或 MySQL
3. **安全性**: 生产环境请修改 `SECRET_KEY` 并配置 HTTPS
4. **验证码有效期**: 默认 10 分钟，可在 `config.py` 中修改

---

## 下一步建议

1. 添加 JWT 认证
2. 实现密码重置功能
3. 添加邮箱验证流程（注册后验证邮箱）
4. 实现登录功能
5. 添加日志记录
6. 添加限流功能

