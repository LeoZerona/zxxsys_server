# email_verifications 表说明

## 📋 表的作用

`email_verifications` 表用于**存储和管理邮箱验证码**，是用户注册流程中的核心安全组件。

---

## 🗂️ 表结构

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | Integer | 主键，自增 |
| `email` | String(120) | 邮箱地址（索引） |
| `code` | String(10) | 验证码（6位数字） |
| `is_used` | Boolean | 是否已使用（默认 False） |
| `created_at` | DateTime | 创建时间 |
| `expires_at` | DateTime | 过期时间 |

---

## 🎯 主要功能

### 1. **存储验证码**
当用户请求发送验证码时，系统会：
- 生成 6 位随机数字验证码
- 保存到 `email_verifications` 表
- 发送邮件给用户

### 2. **验证码时效性控制**
- 每个验证码有 **10 分钟**有效期（`expires_at`）
- 超过有效期后自动失效
- 注册时会检查验证码是否过期

### 3. **防止验证码重复使用**
- `is_used` 字段标记验证码是否已使用
- 验证成功后，验证码会被标记为 `is_used = True`
- 已使用的验证码无法再次使用

### 4. **发送频率限制**
- 通过查询该表，检查同一邮箱的最近验证码发送时间
- **1 分钟内**只能发送一次验证码（防止恶意刷验证码）

---

## 📊 数据流转过程

### 流程 1: 发送验证码

```
用户请求发送验证码
    ↓
检查 1 分钟内是否已发送过（查询 email_verifications 表）
    ↓
生成新的验证码（6位数字）
    ↓
保存到 email_verifications 表
    - email: 用户邮箱
    - code: 验证码
    - is_used: False
    - created_at: 当前时间
    - expires_at: 当前时间 + 10分钟
    ↓
发送邮件给用户
```

### 流程 2: 验证验证码（注册时）

```
用户提交注册请求（包含验证码）
    ↓
查询 email_verifications 表
    - 查找 email 和 code 匹配的记录
    - is_used = False（未使用）
    ↓
检查验证码是否过期（expires_at > 当前时间）
    ↓
验证通过后：
    - 标记 is_used = True
    - 创建用户账号
```

---

## 💡 实际使用示例

### 示例 1: 发送验证码后的数据

```sql
-- 用户 test@example.com 请求发送验证码
INSERT INTO email_verifications (email, code, is_used, created_at, expires_at)
VALUES ('test@example.com', '123456', 0, '2024-01-15 10:00:00', '2024-01-15 10:10:00');
```

### 示例 2: 验证码使用后的数据

```sql
-- 用户使用验证码注册成功后
UPDATE email_verifications 
SET is_used = 1 
WHERE email = 'test@example.com' AND code = '123456';
```

### 示例 3: 查询验证码状态

```sql
-- 查询某个邮箱的验证码
SELECT * FROM email_verifications 
WHERE email = 'test@example.com' 
ORDER BY created_at DESC 
LIMIT 1;
```

---

## 🔒 安全特性

### 1. **验证码一次性使用**
- 每个验证码只能使用一次
- 防止验证码被重复利用

### 2. **时效性控制**
- 验证码 10 分钟后自动过期
- 防止长时间有效的验证码被恶意使用

### 3. **发送频率限制**
- 1 分钟内只能发送一次
- 防止恶意刷验证码攻击

### 4. **邮箱与验证码绑定**
- 验证码与邮箱地址绑定
- 不同邮箱的验证码互不干扰

---

## 📈 表数据特点

### 正常情况下的数据增长
- 每次发送验证码：新增 1 条记录
- 每次成功注册：1 条记录被标记为 `is_used = True`
- 验证码过期：记录保留，但不会被使用

### 数据清理建议
```sql
-- 清理已使用且超过 7 天的验证码记录
DELETE FROM email_verifications 
WHERE is_used = 1 
AND created_at < DATE_SUB(NOW(), INTERVAL 7 DAY);

-- 清理已过期且未使用的验证码（超过 1 天）
DELETE FROM email_verifications 
WHERE is_used = 0 
AND expires_at < DATE_SUB(NOW(), INTERVAL 1 DAY);
```

---

## 🔍 常见查询场景

### 1. 查看某个邮箱的所有验证码记录
```sql
SELECT * FROM email_verifications 
WHERE email = 'user@example.com' 
ORDER BY created_at DESC;
```

### 2. 查看未使用的验证码
```sql
SELECT * FROM email_verifications 
WHERE is_used = 0 
AND expires_at > NOW();
```

### 3. 查看过期的验证码
```sql
SELECT * FROM email_verifications 
WHERE expires_at < NOW() 
AND is_used = 0;
```

### 4. 统计验证码发送次数
```sql
SELECT email, COUNT(*) as send_count 
FROM email_verifications 
GROUP BY email 
ORDER BY send_count DESC;
```

---

## ⚠️ 注意事项

1. **数据隐私**
   - 表中存储的验证码是敏感信息
   - 生产环境应定期清理历史数据

2. **性能优化**
   - `email` 字段已建立索引，查询速度快
   - 建议定期清理过期和已使用的记录

3. **数据保留策略**
   - 已使用的验证码：可保留 7-30 天（用于审计）
   - 未使用的过期验证码：可立即删除或保留 1-7 天

4. **万能验证码**
   - 使用万能验证码（如 `123456`）时，不会在该表中创建记录
   - 这是开发测试的特殊情况

---

## 🛠️ 相关代码位置

- **模型定义**: `models.py` - `EmailVerification` 类
- **发送验证码**: `email_service.py` - `send_verification_code()` 函数
- **验证验证码**: `email_service.py` - `verify_code()` 函数
- **API 接口**: `app.py` - `/api/send-verification-code` 和 `/api/register`

---

**总结**: `email_verifications` 表是邮箱验证系统的核心存储，负责管理验证码的生命周期、时效性和使用状态，确保注册流程的安全性和可靠性。

