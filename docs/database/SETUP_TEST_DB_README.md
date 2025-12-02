# 在 test 数据库中创建表 - 使用说明

## 快速开始

### 方法 1: 使用简化脚本（推荐）

1. **编辑 `setup_test_db.py` 文件**，修改数据库配置：

   ```python
   # 如果是 MySQL
   DATABASE_TYPE = 'mysql'
   MYSQL_CONFIG = {
       'user': 'root',
       'password': '你的密码',  # 修改这里
       'host': 'localhost',
       'port': '3306'
   }
   
   # 如果是 PostgreSQL
   DATABASE_TYPE = 'postgresql'
   POSTGRESQL_CONFIG = {
       'user': 'postgres',
       'password': '你的密码',  # 修改这里
       'host': 'localhost',
       'port': '5432'
   }
   
   # 如果是 SQLite
   DATABASE_TYPE = 'sqlite'  # 无需其他配置
   ```

2. **运行脚本**：

   ```bash
   # 激活虚拟环境（如果使用）
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   
   # 运行脚本
   python setup_test_db.py
   ```

### 方法 2: 使用交互式脚本

```bash
python create_tables_in_test_db.py
```

脚本会提示你选择数据库类型并输入配置信息。

### 方法 3: 直接修改简单脚本

编辑 `create_tables_in_test_db_simple.py`，取消注释并修改对应的数据库配置行，然后运行。

## 数据库类型配置示例

### SQLite

```python
DATABASE_TYPE = 'sqlite'
# 会自动创建 test.db 文件
```

### MySQL

```python
DATABASE_TYPE = 'mysql'
MYSQL_CONFIG = {
    'user': 'root',
    'password': '123456',
    'host': 'localhost',
    'port': '3306'
}
```

**注意**: 需要先安装 MySQL 驱动：
```bash
pip install pymysql
```

### PostgreSQL

```python
DATABASE_TYPE = 'postgresql'
POSTGRESQL_CONFIG = {
    'user': 'postgres',
    'password': '123456',
    'host': 'localhost',
    'port': '5432'
}
```

**注意**: 需要先安装 PostgreSQL 驱动：
```bash
pip install psycopg2-binary
```

## 前提条件

1. **确保 test 数据库已创建**：
   
   - **MySQL**: 
     ```sql
     CREATE DATABASE IF NOT EXISTS test CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
     ```
   
   - **PostgreSQL**: 
     ```sql
     CREATE DATABASE test;
     ```
   
   - **SQLite**: 无需手动创建，脚本会自动创建 `test.db` 文件

2. **确保数据库用户有权限**：
   - 需要有 CREATE TABLE 权限
   - 需要有 CREATE INDEX 权限

3. **安装必要的驱动**（如果使用 MySQL 或 PostgreSQL）

## 运行结果

成功运行后，你会看到：

```
============================================================
在 test 数据库中创建表
============================================================

数据库类型: MYSQL
数据库 URI: mysql+pymysql://***:***@localhost:3306/test

正在连接到数据库...
✓ 数据库连接成功

开始创建表...

============================================================
✓ 表创建成功！
============================================================

已创建的表 (2 个):
  ✓ users
  ✓ email_verifications

------------------------------------------------------------
users 表结构:
------------------------------------------------------------
  • id                  INTEGER                       可空
  • email               VARCHAR(120)                  不可空 [唯一]
  • password_hash       VARCHAR(255)                  不可空
  • created_at          DATETIME                      可空
  • updated_at          DATETIME                      可空
  • is_active           BOOLEAN                       可空

============================================================
✓ 完成！所有表已成功创建在 test 数据库中。
============================================================
```

## 常见问题

### Q: 提示缺少数据库驱动？

**A**: 根据你使用的数据库类型安装对应的驱动：

- MySQL: `pip install pymysql`
- PostgreSQL: `pip install psycopg2-binary`

### Q: 连接数据库失败？

**A**: 检查：
1. 数据库服务是否正在运行
2. 用户名和密码是否正确
3. 主机和端口是否正确
4. test 数据库是否已创建
5. 防火墙是否阻止连接

### Q: 权限不足？

**A**: 确保数据库用户有 CREATE TABLE 权限：

**MySQL**:
```sql
GRANT ALL PRIVILEGES ON test.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;
```

**PostgreSQL**:
```sql
GRANT ALL PRIVILEGES ON DATABASE test TO your_user;
```

### Q: 表已存在？

**A**: 如果表已存在，脚本不会重复创建（使用了 `create_all()`）。如果你想重新创建，先删除现有表：

```sql
DROP TABLE IF EXISTS email_verifications;
DROP TABLE IF EXISTS users;
```

## 验证表是否创建成功

### MySQL
```sql
USE test;
SHOW TABLES;
DESCRIBE users;
```

### PostgreSQL
```sql
\c test
\dt
\d users
```

### SQLite
```bash
sqlite3 test.db
.tables
.schema users
```

## 下一步

表创建成功后，你可以：

1. 修改 `config.py` 或 `.env` 文件，将应用连接到 test 数据库
2. 运行应用测试数据库连接
3. 使用 API 测试注册功能

