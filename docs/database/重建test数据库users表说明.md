# 在 test 数据库中重建 users 表

## 📋 说明

此脚本专门用于在 **test 数据库**中删除并重建 users 表，确保包含最新的 `role` 权限字段。

⚠️ **注意**：此操作**仅影响 test 数据库中的 users 表**，不会影响其他表（如 `email_verifications`）。

---

## 🚀 使用方法

### 步骤 1: 配置数据库连接

编辑 `rebuild_users_table_in_test_db.py` 文件，根据你的数据库类型修改配置：

#### SQLite

```python
DATABASE_TYPE = 'sqlite'
# 无需其他配置，会自动使用 test.db 文件
```

#### MySQL

```python
DATABASE_TYPE = 'mysql'
MYSQL_CONFIG = {
    'user': 'root',
    'password': '你的MySQL密码',  # 修改这里
    'host': 'localhost',
    'port': '3306'
}
```

#### PostgreSQL

```python
DATABASE_TYPE = 'postgresql'
POSTGRESQL_CONFIG = {
    'user': 'postgres',
    'password': '你的PostgreSQL密码',  # 修改这里
    'host': 'localhost',
    'port': '5432'
}
```

### 步骤 2: 执行脚本

```bash
python rebuild_users_table_in_test_db.py
```

### 步骤 3: 确认操作

输入 `yes` 确认继续。

---

## ✅ 执行效果

脚本会：
1. ✅ 连接到 test 数据库
2. ✅ 删除现有的 users 表（如果存在）
3. ✅ 创建新的 users 表（包含 role 字段）
4. ✅ 自动创建索引（email 和 role）
5. ✅ 显示表结构验证信息

---

## 📊 重建后的表结构

### users 表字段

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER/INT/SERIAL | 主键 | PRIMARY KEY, AUTO_INCREMENT |
| email | VARCHAR(120) | 邮箱地址 | UNIQUE, NOT NULL, 已建索引 |
| password_hash | VARCHAR(255) | 密码哈希 | NOT NULL |
| **role** | VARCHAR(20) | 用户权限 | NOT NULL, DEFAULT 'user', 已建索引 |
| created_at | DATETIME/TIMESTAMP | 创建时间 | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME/TIMESTAMP | 更新时间 | DEFAULT CURRENT_TIMESTAMP |
| is_active | BOOLEAN/TINYINT(1) | 是否激活 | DEFAULT 1/TRUE |

### role 字段说明

- **默认值**：`'user'`
- **允许值**：
  - `'super_admin'` - 超级管理员
  - `'admin'` - 管理员
  - `'user'` - 普通用户（默认）

---

## 🔍 验证步骤

### 1. 检查表是否存在

**SQLite**:
```bash
sqlite3 test.db ".tables"
```

**MySQL**:
```sql
USE test;
SHOW TABLES;
```

**PostgreSQL**:
```sql
\c test
\dt
```

### 2. 查看表结构

**SQLite**:
```bash
sqlite3 test.db ".schema users"
```

**MySQL**:
```sql
USE test;
DESCRIBE users;
```

**PostgreSQL**:
```sql
\c test
\d users
```

### 3. 验证 role 字段

```sql
-- 查看表结构中的 role 字段
SELECT * FROM users LIMIT 0;  -- 查看字段
```

---

## ⚠️ 常见问题

### 问题 1: 连接失败

**MySQL**:
- 检查 MySQL 服务是否运行
- 检查用户名和密码是否正确
- 确认 test 数据库是否存在

**PostgreSQL**:
- 检查 PostgreSQL 服务是否运行
- 检查用户名和密码是否正确
- 确认 test 数据库是否存在

**解决方案**:
```bash
# MySQL - 创建数据库（如果不存在）
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS test;"

# PostgreSQL - 创建数据库（如果不存在）
createdb -U postgres test
```

### 问题 2: 权限不足

确保数据库用户有足够的权限：
- 删除表
- 创建表
- 创建索引

**解决方案**:
```sql
-- MySQL
GRANT ALL PRIVILEGES ON test.* TO 'your_user'@'localhost';

-- PostgreSQL
GRANT ALL PRIVILEGES ON DATABASE test TO your_user;
```

### 问题 3: 驱动未安装

**MySQL**:
```bash
pip install pymysql
```

**PostgreSQL**:
```bash
pip install psycopg2-binary
```

---

## 📝 执行示例

### 成功执行示例

```
============================================================
在 test 数据库中重建 users 表
============================================================
数据库类型: mysql
数据库 URI: mysql+pymysql://root:****@localhost:3306/test?charset=utf8mb4

当前数据库中的表: ['email_verifications', 'users']

⚠️  检测到 users 表存在，正在删除...
✅ users 表已删除

正在创建新的 users 表...
✅ users 表创建成功

表结构验证:
  - id: INT NOT NULL
  - email: VARCHAR(120) NOT NULL
  - password_hash: VARCHAR(255) NOT NULL
  - role: VARCHAR(20) NOT NULL DEFAULT user
  - created_at: DATETIME NULL
  - updated_at: DATETIME NULL
  - is_active: TINYINT(1) NULL DEFAULT 1

索引验证:
  - idx_users_email: ['email']
  - idx_users_role: ['role']

============================================================
✅ 重建完成！
============================================================
```

---

## 🔗 相关文件

- `rebuild_users_table_in_test_db.py` - 本脚本
- `setup_test_db.py` - test 数据库初始化脚本
- `models.py` - 用户模型定义

---

**确保修改脚本中的数据库配置后再执行！** 🚀

