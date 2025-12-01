# 数据库更新 SQL 语句

## 📋 更新说明

本次更新主要为 `users` 表添加 `role` 字段，用于存储用户权限信息。

**更新内容**：
- 添加 `role` 字段（VARCHAR(20)，默认值 'user'）
- 创建 `role` 字段的索引
- 为现有用户设置默认权限

---

## 🗄️ SQLite 版本

### 方法 1: 直接执行 SQL（推荐）

```sql
-- 1. 添加 role 字段
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL;

-- 2. 为现有用户设置默认权限（如果 role 为 NULL 或空）
UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';

-- 3. 创建索引（提高查询性能）
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
```

### 执行方式

**方式 A: 使用 sqlite3 命令行**
```bash
sqlite3 app.db < update_users_table_add_role.sql
```

**方式 B: 在 Python 中执行**
```python
import sqlite3

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# 执行 SQL
cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL;")
cursor.execute("UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);")

conn.commit()
conn.close()
```

---

## 🗄️ MySQL 版本

```sql
-- 1. 添加 role 字段（在 password_hash 之后）
ALTER TABLE users 
ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user' 
AFTER password_hash;

-- 2. 为现有用户设置默认权限（如果 role 为 NULL 或空）
UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';

-- 3. 创建索引
CREATE INDEX idx_users_role ON users(role);
```

### 执行方式

**方式 A: 使用 mysql 命令行**
```bash
mysql -u username -p database_name < update_users_table_add_role_mysql.sql
```

**方式 B: 在 MySQL Workbench 中执行**
- 打开 MySQL Workbench
- 连接到数据库
- 执行上述 SQL 语句

**方式 C: 在 Python 中执行**
```python
import pymysql

conn = pymysql.connect(
    host='localhost',
    user='username',
    password='password',
    database='database_name'
)
cursor = conn.cursor()

cursor.execute("""
    ALTER TABLE users 
    ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user' 
    AFTER password_hash;
""")

cursor.execute("UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';")
cursor.execute("CREATE INDEX idx_users_role ON users(role);")

conn.commit()
conn.close()
```

---

## 🗄️ PostgreSQL 版本

```sql
-- 1. 添加 role 字段
ALTER TABLE users 
ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user';

-- 2. 为现有用户设置默认权限（如果 role 为 NULL 或空）
UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';

-- 3. 创建索引
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
```

### 执行方式

**方式 A: 使用 psql 命令行**
```bash
psql -U username -d database_name -f update_users_table_add_role_postgresql.sql
```

**方式 B: 在 pgAdmin 中执行**
- 打开 pgAdmin
- 连接到数据库
- 在查询工具中执行上述 SQL 语句

**方式 C: 在 Python 中执行**
```python
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    user='username',
    password='password',
    database='database_name'
)
cursor = conn.cursor()

cursor.execute("""
    ALTER TABLE users 
    ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user';
""")

cursor.execute("UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';")
cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);")

conn.commit()
conn.close()
```

---

## 📝 完整的迁移 SQL 文件

### SQLite 完整脚本

保存为 `update_users_table_add_role_sqlite.sql`:

```sql
-- ============================================================================
-- 数据库迁移：为用户表添加权限字段 (SQLite 版本)
-- ============================================================================
-- 说明：如果 users 表已存在，执行此 SQL 添加 role 字段
-- 执行方式：sqlite3 app.db < update_users_table_add_role_sqlite.sql
-- ============================================================================

-- 检查并添加 role 字段
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL;

-- 为现有用户设置默认权限
UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';

-- 创建索引（提高查询性能）
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 验证更新
SELECT sql FROM sqlite_master WHERE type='table' AND name='users';
```

### MySQL 完整脚本

保存为 `update_users_table_add_role_mysql.sql`:

```sql
-- ============================================================================
-- 数据库迁移：为用户表添加权限字段 (MySQL 版本)
-- ============================================================================
-- 说明：如果 users 表已存在，执行此 SQL 添加 role 字段
-- 执行方式：mysql -u username -p database_name < update_users_table_add_role_mysql.sql
-- ============================================================================

-- 检查并添加 role 字段（在 password_hash 之后）
ALTER TABLE users 
ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user' 
AFTER password_hash;

-- 为现有用户设置默认权限
UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';

-- 创建索引
CREATE INDEX idx_users_role ON users(role);

-- 验证更新
DESCRIBE users;
```

### PostgreSQL 完整脚本

保存为 `update_users_table_add_role_postgresql.sql`:

```sql
-- ============================================================================
-- 数据库迁移：为用户表添加权限字段 (PostgreSQL 版本)
-- ============================================================================
-- 说明：如果 users 表已存在，执行此 SQL 添加 role 字段
-- 执行方式：psql -U username -d database_name -f update_users_table_add_role_postgresql.sql
-- ============================================================================

-- 检查并添加 role 字段
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user';

-- 为现有用户设置默认权限
UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- 验证更新
\d users;
```

---

## ✅ 验证更新

### SQLite
```sql
-- 查看表结构
.schema users

-- 查看现有用户的权限
SELECT id, email, role FROM users LIMIT 5;
```

### MySQL
```sql
-- 查看表结构
DESCRIBE users;

-- 查看现有用户的权限
SELECT id, email, role FROM users LIMIT 5;
```

### PostgreSQL
```sql
-- 查看表结构
\d users

-- 查看现有用户的权限
SELECT id, email, role FROM users LIMIT 5;
```

---

## 🔍 字段说明

### role 字段

- **字段名**: `role`
- **类型**: `VARCHAR(20)`
- **默认值**: `'user'`
- **是否为空**: `NOT NULL`
- **允许值**:
  - `'super_admin'` - 超级管理员（最高权限）
  - `'admin'` - 管理员
  - `'user'` - 普通用户（默认）

### 索引

- **索引名**: `idx_users_role`
- **作用**: 提高按权限查询的性能
- **使用场景**: 
  - 查询所有管理员：`SELECT * FROM users WHERE role = 'admin'`
  - 查询超级管理员：`SELECT * FROM users WHERE role = 'super_admin'`

---

## ⚠️ 注意事项

1. **备份数据**
   - 执行迁移前，请先备份数据库
   - SQLite: `cp app.db app.db.backup`
   - MySQL: `mysqldump -u username -p database_name > backup.sql`
   - PostgreSQL: `pg_dump -U username database_name > backup.sql`

2. **检查表是否存在**
   - 如果 `users` 表不存在，需要先创建表
   - 参考 `create_users_table_only.sql` 文件

3. **检查字段是否已存在**
   - 如果 `role` 字段已存在，执行 `ALTER TABLE` 会报错
   - 可以先查询表结构确认

4. **索引创建**
   - 如果表数据量大，创建索引可能需要一些时间
   - 索引创建不会影响现有数据

---

## 🚀 快速执行（Python 脚本）

你也可以使用 Python 脚本自动检测数据库类型并执行相应的 SQL：

```python
"""自动数据库迁移脚本"""
from app import app, db
from sqlalchemy import text

def migrate_add_role():
    """添加用户权限字段"""
    with app.app_context():
        try:
            # 检测数据库类型
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            
            if 'sqlite' in db_url.lower():
                # SQLite
                db.session.execute(text("""
                    ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL;
                """))
            elif 'mysql' in db_url.lower():
                # MySQL
                db.session.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user' 
                    AFTER password_hash;
                """))
            elif 'postgresql' in db_url.lower() or 'postgres' in db_url.lower():
                # PostgreSQL
                db.session.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user';
                """))
            else:
                print("不支持的数据库类型")
                return False
            
            # 为现有用户设置默认权限
            db.session.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';"))
            
            # 创建索引
            if 'sqlite' in db_url.lower():
                db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);"))
            elif 'mysql' in db_url.lower():
                db.session.execute(text("CREATE INDEX idx_users_role ON users(role);"))
            elif 'postgresql' in db_url.lower() or 'postgres' in db_url.lower():
                db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);"))
            
            db.session.commit()
            print("✅ 数据库迁移成功！")
            return True
        
        except Exception as e:
            db.session.rollback()
            if 'duplicate column name' in str(e).lower() or 'already exists' in str(e).lower():
                print("ℹ️  role 字段已存在，跳过迁移")
                return True
            else:
                print(f"❌ 迁移失败: {str(e)}")
                import traceback
                traceback.print_exc()
                return False

if __name__ == '__main__':
    migrate_add_role()
```

---

## 📚 相关文件

- `update_users_table_add_role.sql` - 通用迁移 SQL（已存在）
- `create_users_table_only.sql` - 创建用户表的完整 SQL（已包含 role 字段）
- `migrate_add_user_role.py` - Python 迁移脚本（已存在）

---

## 🔗 快速链接

- [功能更新说明](./功能更新说明.md)
- [完整更新说明](./完整更新说明.md)
- [API 文档](./API.md)

