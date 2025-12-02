# 快速创建 users 表

## 🚀 使用方法

### 步骤 1: 编辑配置

打开 `create_users_table.py` 文件，修改数据库配置：

#### 方式 A: 直接使用连接字符串（最简单）

在文件末尾取消注释并修改：

```python
# MySQL 示例
DATABASE_URI = 'mysql+pymysql://root:你的密码@localhost:3306/test?charset=utf8mb4'

# PostgreSQL 示例
# DATABASE_URI = 'postgresql://postgres:你的密码@localhost:5432/test'

# SQLite 示例
# DATABASE_URI = 'sqlite:///test.db'
```

#### 方式 B: 使用配置项

```python
DATABASE_TYPE = 'mysql'  # 'sqlite', 'mysql', 'postgresql'

MYSQL_CONFIG = {
    'user': 'root',
    'password': '你的密码',  # 修改这里
    'host': 'localhost',
    'port': '3306',
    'database': 'test'
}
```

### 步骤 2: 运行脚本

```bash
python create_users_table.py
```

### 步骤 3: 选择操作（如果表已存在）

- **选项 1**: 删除现有表并重新创建（会丢失所有数据）
- **选项 2**: 仅添加缺失的字段（保留数据）
- **选项 3**: 取消

---

## ✨ 脚本功能

1. ✅ **自动检测表是否存在**
2. ✅ **智能处理已存在的表**（可选择删除重建或添加字段）
3. ✅ **显示完整的表结构信息**
4. ✅ **自动创建索引**
5. ✅ **友好的错误提示**

---

## 📊 生成的表结构

| 字段名 | 类型 | 说明 | 约束 |
|--------|------|------|------|
| id | INTEGER/INT/SERIAL | 主键 | PRIMARY KEY, AUTO_INCREMENT |
| email | VARCHAR(120) | 邮箱地址 | UNIQUE, NOT NULL, 已建索引 |
| password_hash | VARCHAR(255) | 密码哈希 | NOT NULL |
| **role** | VARCHAR(20) | 用户权限 | NOT NULL, DEFAULT 'user', 已建索引 |
| created_at | DATETIME/TIMESTAMP | 创建时间 | DEFAULT CURRENT_TIMESTAMP |
| updated_at | DATETIME/TIMESTAMP | 更新时间 | DEFAULT CURRENT_TIMESTAMP |
| is_active | BOOLEAN/TINYINT(1) | 是否激活 | DEFAULT 1/TRUE |

---

## ⚡ 快速配置示例

### MySQL

```python
# 在脚本末尾修改
DATABASE_URI = 'mysql+pymysql://root:123456@localhost:3306/test?charset=utf8mb4'
```

### PostgreSQL

```python
DATABASE_URI = 'postgresql://postgres:123456@localhost:5432/test'
```

### SQLite

```python
DATABASE_URI = 'sqlite:///test.db'
```

---

## 📝 执行示例

```
======================================================================
生成 users 表
======================================================================

数据库类型: MYSQL
数据库: localhost:3306/test

users 表不存在，正在创建...

✅ users 表创建成功

----------------------------------------------------------------------
表结构信息
----------------------------------------------------------------------

字段列表:
  • id                   INTEGER(11)              NOT NULL
  • email                VARCHAR(120)             NOT NULL
  • password_hash        VARCHAR(255)             NOT NULL
  • role                 VARCHAR(20)              NOT NULL DEFAULT user
  • created_at           DATETIME                 NULL
  • updated_at           DATETIME                 NULL
  • is_active            TINYINT(1)               NULL DEFAULT 1

索引列表:
  • idx_users_email      列: ['email']
  • idx_users_role       列: ['role']

======================================================================
✅ 完成！users 表已就绪
======================================================================

表包含以下字段:
  - id: 主键，自增
  - email: 邮箱地址，唯一，已建立索引
  - password_hash: 密码哈希值
  - role: 用户权限（'super_admin', 'admin', 'user'），默认 'user'，已建立索引
  - created_at: 创建时间
  - updated_at: 更新时间
  - is_active: 是否激活
```

---

## ⚠️ 注意事项

1. **确保数据库已创建**
   - MySQL: `CREATE DATABASE test;`
   - PostgreSQL: `CREATE DATABASE test;`
   - SQLite: 会自动创建文件

2. **安装数据库驱动**
   ```bash
   # MySQL
   pip install pymysql
   
   # PostgreSQL
   pip install psycopg2-binary
   ```

3. **如果表已存在**
   - 选择选项 1 会**删除所有数据**
   - 选择选项 2 会**保留数据**并添加缺失字段

---

**直接运行脚本即可！** 🚀

