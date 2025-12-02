# CORS 跨域配置说明

## 📋 概述

本项目已配置完善的 CORS（跨域资源共享）支持，可以灵活适应开发环境和生产环境的需求。

---

## 🚀 快速配置

### 方式一：使用环境变量（推荐）

创建或编辑 `.env` 文件：

#### 开发环境 - 允许所有来源（仅本地开发使用）

```env
FLASK_ENV=development
CORS_ORIGINS=*
```

#### 开发环境 - 指定多个来源

```env
FLASK_ENV=development
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:8080
```

#### 生产环境 - 指定生产域名

```env
FLASK_ENV=production
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

---

## 🔧 配置选项说明

### 1. 环境变量

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| `FLASK_ENV` | 环境类型 | `development` 或 `production` |
| `CORS_ORIGINS` | 允许的来源 | `*` 或 `http://localhost:5173,https://example.com` |

### 2. CORS_ORIGINS 特殊值

- `*` 或 `all`: 允许所有来源（**仅开发环境推荐**）
- 具体域名列表: 用逗号分隔多个域名
- 留空: 使用默认配置

### 3. 默认配置

**开发环境默认允许的来源：**
- `http://localhost:5173` (Vite)
- `http://localhost:3000` (Create React App)
- `http://localhost:8080` (Vue CLI)
- `http://127.0.0.1:5173`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:8080`
- `null` (允许直接访问，file:// 协议)

**生产环境默认：**
- 不允许所有来源（需要显式配置）

---

## 📝 支持的请求类型

CORS 配置支持以下 HTTP 方法：
- ✅ GET
- ✅ POST
- ✅ PUT
- ✅ DELETE
- ✅ PATCH
- ✅ OPTIONS (预检请求)

---

## 🔐 允许的请求头

- `Content-Type`
- `Authorization`
- `X-Requested-With`

---

## ✅ 凭证支持

当使用具体域名（非 `*`）时，支持携带凭证（cookies、认证信息等）。

---

## 🎯 使用场景

### 场景 1: 本地开发（Vue3 项目）

**.env 文件：**
```env
FLASK_ENV=development
CORS_ORIGINS=http://localhost:5173
```

### 场景 2: 多个前端项目开发

**.env 文件：**
```env
FLASK_ENV=development
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:8080
```

### 场景 3: 开发时允许所有来源（不推荐，仅临时使用）

**.env 文件：**
```env
FLASK_ENV=development
CORS_ORIGINS=*
```

### 场景 4: 生产环境

**.env 文件：**
```env
FLASK_ENV=production
CORS_ORIGINS=https://app.yourdomain.com,https://admin.yourdomain.com
```

---

## 🔍 验证 CORS 配置

启动服务后，控制台会显示当前 CORS 配置：

```
✅ CORS 配置: 允许的来源列表:
   - http://localhost:5173
   - http://localhost:3000
   - null
```

或

```
⚠️  CORS 配置: 允许所有来源访问（仅开发环境）
```

---

## 🐛 常见问题

### 1. 仍然出现跨域错误

**解决方法：**
1. 检查 `.env` 文件是否正确配置
2. 确认前端请求的域名在允许列表中
3. 重启后端服务使配置生效
4. 检查浏览器控制台的完整错误信息

### 2. 预检请求（OPTIONS）失败

**原因：** 某些浏览器会先发送 OPTIONS 预检请求

**解决方法：** Flask-CORS 会自动处理，确保配置正确即可

### 3. 生产环境需要添加新域名

**解决方法：**
```env
CORS_ORIGINS=https://old-domain.com,https://new-domain.com
```

重启服务即可生效。

---

## 📚 技术细节

### CORS 响应头

当请求来自允许的来源时，响应会包含以下头部：

```
Access-Control-Allow-Origin: http://localhost:5173
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS, PATCH
Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With
```

### 预检请求（Preflight）

对于复杂请求（如 POST 带 JSON），浏览器会先发送 OPTIONS 预检请求，Flask-CORS 会自动处理并返回正确的响应。

---

## ⚠️ 安全建议

1. **生产环境不要使用 `CORS_ORIGINS=*`**
   - 这会允许任何网站访问你的 API
   - 存在安全风险

2. **使用 HTTPS 协议**
   - 生产环境应使用 HTTPS
   - 确保 CORS_ORIGINS 中的域名也使用 HTTPS

3. **定期检查允许的来源**
   - 移除不再使用的域名
   - 只添加必要的域名

4. **监控 CORS 错误**
   - 检查日志中的 CORS 相关信息
   - 及时处理跨域问题

---

## 🔄 更新日志

- ✅ 支持开发环境和生产环境配置
- ✅ 支持允许所有来源（开发环境）
- ✅ 支持直接访问（file:// 协议）
- ✅ 支持携带凭证（credentials）
- ✅ 自动处理预检请求（OPTIONS）
- ✅ 控制台显示当前配置

---

**配置完成后，重启服务即可生效！** 🚀

