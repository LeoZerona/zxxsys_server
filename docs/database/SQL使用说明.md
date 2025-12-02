# SQL 表创建语句使用说明

## 文件说明

### 1. `create_users_table_only.sql` 
**仅包含用户表（users）的创建语句**，如果你只需要创建用户表，使用这个文件。

### 2. `create_tables.sql`
**包含所有表的创建语句**（用户表和邮箱验证码表），如果你想创建完整的数据库结构，使用这个文件。

## 根据数据库类型选择

### SQLite（默认）

项目默认使用 SQLite 数据库，直接使用文件中的 SQLite 版本即可。

```sql
-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- 创建邮箱索引
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
```

### MySQL

如果使用 MySQL，请使用 MySQL 版本的 SQL（去掉注释 `/* */`）。

```sql
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active TINYINT(1) DEFAULT 1,
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### PostgreSQL

如果使用 PostgreSQL，请使用 PostgreSQL 版本的 SQL（去掉注释 `/* */`）。

```sql
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
```

## 使用方法

### 方法 1: 使用 SQL 客户端执行

1. 打开你的数据库管理工具（如 MySQL Workbench、pgAdmin、DBeaver 等）
2. 连接到数据库
3. 打开对应的 SQL 文件
4. 复制对应数据库版本的 SQL 语句
5. 执行 SQL 语句

### 方法 2: 使用命令行执行

#### SQLite
```bash
sqlite3 app.db < create_users_table_only.sql
```

#### MySQL
```bash
mysql -u username -p database_name < create_users_table_only.sql
```

#### PostgreSQL
```bash
psql -U username -d database_name -f create_users_table_only.sql
```

### 方法 3: 使用 Python 执行

如果你已经在使用 Flask-SQLAlchemy，通常不需要手动执行 SQL，直接运行：

```bash
python init_db.py
```

或者直接运行应用，数据库表会自动创建（在 `app.py` 中已配置）。

## 表结构说明

### users 表

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INTEGER | 主键，自增 |
| email | VARCHAR(120) | 邮箱地址，唯一，不可为空，已建立索引 |
| password_hash | VARCHAR(255) | 密码哈希值，不可为空 |
| created_at | DATETIME | 创建时间，默认当前时间 |
| updated_at | DATETIME | 更新时间，默认当前时间，更新时自动更新 |
| is_active | BOOLEAN | 是否激活，默认 true |

## 验证表是否创建成功

### SQLite
```bash
sqlite3 app.db
.tables
.schema users
```

### MySQL
```sql
SHOW TABLES;
DESCRIBE users;
```

### PostgreSQL
```sql
\dt
\d users
```

## 注意事项

1. **唯一约束**: `email` 字段有唯一约束，不能重复
2. **索引**: `email` 字段已建立索引，提高查询性能
3. **自动更新**: `updated_at` 字段在更新记录时会自动更新（MySQL 和 PostgreSQL）
4. **密码安全**: `password_hash` 存储的是加密后的密码，不是明文

## 如果需要删除表（谨慎操作）

```sql
-- SQLite / MySQL / PostgreSQL
DROP TABLE IF EXISTS users;
DROP INDEX IF EXISTS idx_users_email;
```

## 常见问题

### Q: 为什么使用 `CREATE TABLE IF NOT EXISTS`？
A: 这样可以安全地多次执行 SQL，如果表已存在不会报错。

### Q: SQLite 和 MySQL/PostgreSQL 的区别？
A: 
- SQLite: 使用 `INTEGER PRIMARY KEY AUTOINCREMENT`
- MySQL: 使用 `INT AUTO_INCREMENT PRIMARY KEY`
- PostgreSQL: 使用 `SERIAL PRIMARY KEY`

### Q: 如何更新已存在的表结构？
A: 需要编写 ALTER TABLE 语句，或者删除表后重新创建（会丢失数据）。

