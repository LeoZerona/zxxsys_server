# Flask 后端服务

这是一个基于 Flask 的后端 API 服务，提供邮箱注册功能，支持与 Vue3 + TypeScript 前端项目集成。

## 功能特性

- ✅ 邮箱注册 API
- ✅ SQLite 数据库（可配置为 PostgreSQL/MySQL）
- ✅ 密码加密存储
- ✅ CORS 跨域支持
- ✅ RESTful API 设计
- ✅ 错误处理和验证

## 项目结构

```
.
├── app.py              # Flask 主应用文件
├── config.py           # 配置文件
├── models.py           # 数据库模型
├── init_db.py          # 数据库初始化脚本
├── requirements.txt    # Python 依赖包
├── API.md             # API 接口文档
└── templates/         # HTML 模板（保留原有功能）
```

## 安装和运行

### 1. 安装依赖

确保已激活虚拟环境，然后安装依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量（可选）

创建 `.env` 文件（参考 `.env.example`）：

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///app.db
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. 初始化数据库

```bash
python init_db.py
```

或者直接运行应用，数据库表会在首次启动时自动创建。

### 4. 运行应用

```bash
python app.py
```

应用将在 `http://localhost:5000` 启动。

## API 接口

详细 API 文档请查看 [API.md](API.md)

### 主要接口

- `POST /api/register` - 邮箱注册
- `GET /api/health` - 健康检查
- `GET /api/users/{id}` - 获取用户信息

## 前端调用示例

### 使用 Fetch API

```typescript
const response = await fetch('http://localhost:5000/api/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123',
  }),
});

const data = await response.json();
```

### 使用 Axios

```typescript
import axios from 'axios';

const response = await axios.post('http://localhost:5000/api/register', {
  email: 'user@example.com',
  password: 'password123',
});
```

## 数据库配置

默认使用 SQLite 数据库（`app.db`）。如需使用 PostgreSQL 或 MySQL，请修改 `config.py` 或设置环境变量 `DATABASE_URL`。

### PostgreSQL 示例

```env
DATABASE_URL=postgresql://username:password@localhost/dbname
```

### MySQL 示例

```env
DATABASE_URL=mysql://username:password@localhost/dbname
```

## CORS 配置

默认允许的前端地址：
- `http://localhost:5173` (Vite 默认端口)
- `http://localhost:3000` (Create React App 默认端口)

如需添加其他地址，请修改 `config.py` 中的 `CORS_ORIGINS` 或设置环境变量。

## 注意事项

1. 生产环境请修改 `SECRET_KEY`
2. 生产环境建议使用 PostgreSQL 或 MySQL
3. 建议添加更多的安全措施（如 JWT 认证、限流等）
4. 密码应在前端进行基本验证，后端也会进行验证

## 依赖包

- Flask - Web 框架
- Flask-SQLAlchemy - 数据库 ORM
- Flask-CORS - 跨域支持
- python-dotenv - 环境变量管理
- bcrypt - 密码加密（通过 Werkzeug 使用）

## 开发建议

1. 在生产环境使用环境变量管理敏感信息
2. 添加日志记录
3. 实现更完善的错误处理
4. 添加 API 认证机制（JWT）
5. 添加邮箱验证功能
6. 实现密码重置功能

