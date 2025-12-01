# Flask API 文档

## 基础信息

- **基础 URL**: `http://localhost:5000`
- **内容类型**: `application/json`

## API 接口

### 1. 健康检查

**GET** `/api/health`

检查服务是否正常运行。

**响应示例**:
```json
{
  "status": "healthy",
  "message": "服务运行正常"
}
```

---

### 2. 邮箱注册

**POST** `/api/register`

用户邮箱注册接口。

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "verification_code": "123456"
}
```

**请求参数**:
- `email` (string, required): 用户邮箱地址
- `password` (string, required): 用户密码（至少 6 位）
- `verification_code` (string, required): 邮箱验证码（从发送验证码接口获取）

**成功响应** (201):
```json
{
  "success": true,
  "message": "注册成功",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "role": "user",
    "created_at": "2024-01-01T00:00:00",
    "is_active": true
  }
}
```

**错误响应**:

- 邮箱已存在 (409):
```json
{
  "success": false,
  "message": "该邮箱已被注册"
}
```

- 邮箱格式错误 (400):
```json
{
  "success": false,
  "message": "邮箱格式不正确"
}
```

- 密码太短 (400):
```json
{
  "success": false,
  "message": "密码长度至少为 6 位"
}
```

- 验证码为空 (400):
```json
{
  "success": false,
  "message": "验证码不能为空"
}
```

- 验证码无效或过期 (400):
```json
{
  "success": false,
  "message": "验证码已过期，请重新获取"
}
```

---

### 3. 发送验证码

**POST** `/api/send-verification-code`

发送邮箱验证码到指定邮箱。

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "email": "user@example.com"
}
```

**请求参数**:
- `email` (string, required): 用户邮箱地址

**成功响应** (200):
```json
{
  "success": true,
  "message": "验证码已发送",
  "code": "123456"
}
```
> **注意**：`code` 字段仅在测试模式下返回，生产环境不会返回验证码。

**错误响应**:

- 发送频率过高 (429/500):
```json
{
  "success": false,
  "message": "发送验证码过于频繁，请等待 30秒 后再试",
  "cooldown_seconds": 30
}
```
> **说明**：每个邮箱 1 分钟内只能获取一次验证码。

- 邮箱格式错误 (400):
```json
{
  "success": false,
  "message": "邮箱格式不正确"
}
```

- 邮箱为空 (400):
```json
{
  "success": false,
  "message": "邮箱不能为空"
}
```

---

### 4. 验证验证码

**POST** `/api/verify-code`

验证邮箱验证码是否正确。

**请求头**:
```
Content-Type: application/json
```

**请求体**:
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**请求参数**:
- `email` (string, required): 用户邮箱地址
- `code` (string, required): 验证码

**成功响应** (200):
```json
{
  "success": true,
  "message": "验证码验证成功"
}
```

**错误响应**:

- 验证码无效 (400):
```json
{
  "success": false,
  "message": "验证码无效"
}
```

- 验证码已过期 (400):
```json
{
  "success": false,
  "message": "验证码已过期，请重新获取"
}
```

---

### 5. 获取用户信息

**GET** `/api/users/{user_id}`

根据用户 ID 获取用户信息。

**路径参数**:
- `user_id` (integer, required): 用户 ID

**成功响应** (200):
```json
{
  "success": true,
  "data": {
    "id": 1,
    "email": "user@example.com",
    "role": "user",
    "created_at": "2024-01-01T00:00:00",
    "is_active": true
  }
}
```

**字段说明**:
- `role`: 用户权限，可选值：`super_admin`（超级管理员）、`admin`（管理员）、`user`（普通用户）

## Vue3 + TypeScript 调用示例

```typescript
// 完整注册流程示例
async function completeRegister(email: string, password: string) {
  try {
    // 步骤 1: 发送验证码
    const sendCodeResponse = await fetch('http://localhost:5000/api/send-verification-code', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });
    
    const sendCodeData = await sendCodeResponse.json();
    
    if (!sendCodeData.success) {
      throw new Error(sendCodeData.message);
    }
    
    // 获取验证码（测试模式）
    const verificationCode = sendCodeData.code || prompt('请输入验证码:');
    
    // 步骤 2: 注册
    const registerResponse = await fetch('http://localhost:5000/api/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
        verification_code: verificationCode,
      }),
    });
    
    const registerData = await registerResponse.json();
    
    if (registerData.success) {
      console.log('注册成功:', registerData.data);
      return registerData;
    } else {
      console.error('注册失败:', registerData.message);
      throw new Error(registerData.message);
    }
  } catch (error) {
    console.error('请求失败:', error);
    throw error;
  }
}
```

## 使用 Axios 示例

```typescript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:5000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 发送验证码
export const sendVerificationCode = async (email: string) => {
  const response = await api.post('/send-verification-code', { email });
  return response.data;
};

// 注册
export const registerUser = async (email: string, password: string, verificationCode: string) => {
  const response = await api.post('/register', { 
    email, 
    password,
    verification_code: verificationCode
  });
  return response.data;
};

// 验证验证码
export const verifyCode = async (email: string, code: string) => {
  const response = await api.post('/verify-code', { email, code });
  return response.data;
};
```
```

