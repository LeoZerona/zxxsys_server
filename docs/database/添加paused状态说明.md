# 添加 'paused' 状态到 dedup_tasks 表

## 📋 概述

本文档说明如何为 `dedup_tasks` 表的 `status` 字段添加 `'paused'` 状态支持，以支持任务暂停和继续功能。

---

## 🔧 问题说明

在任务暂停功能中，需要将任务状态设置为 `'paused'`，但数据库表的 `status` 字段（ENUM 类型）可能不包含 `'paused'` 值，导致更新失败。

**错误信息示例**：
```
数据库字段不支持 'paused' 状态。请联系后端开发人员更新数据库 schema，在 status 字段中添加 'paused' 状态。
```

---

## ✅ 解决方案

### 方法一：使用修复脚本（推荐，最简单）

项目已提供直接修复脚本，可以自动检测数据库类型并执行相应的更新：

```bash
# 激活虚拟环境（如果需要）
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# 然后执行修复脚本
python scripts/database/fix_paused_status.py
```

**脚本功能**：
- ✅ 自动检测数据库类型（MySQL/SQLite/PostgreSQL）
- ✅ 检查当前 ENUM 值
- ✅ 自动添加 `'paused'` 状态
- ✅ 如果直接修改失败，自动尝试两步法
- ✅ 验证更新结果

**执行示例**：

```bash
============================================================
修复 dedup_tasks 表的 status 字段
============================================================
数据库连接: localhost:3306/test?charset=utf8mb4

检测到 MySQL 数据库
开始修复 ENUM 字段...

尝试方法1: 直接修改 ENUM...
✅ 方法1 成功：ENUM 字段已更新
✅ 验证成功：当前 ENUM 定义: enum('pending','running','paused','completed','error','cancelled')
✅ 'paused' 状态已成功添加到 ENUM

============================================================
✅ 修复完成！现在可以正常使用暂停功能了
============================================================
```

### 方法二：使用迁移脚本

项目也提供了迁移脚本（功能类似）：

```bash
python scripts/database/migrate_add_paused_status.py
```

**脚本功能**：
- ✅ 自动检测数据库类型（MySQL/SQLite/PostgreSQL）
- ✅ 检查当前 ENUM 值
- ✅ 自动添加 `'paused'` 状态
- ✅ 验证更新结果
- ✅ 支持多种数据库类型

**执行示例**：

```bash
============================================================
数据库迁移：为 dedup_tasks 表添加 'paused' 状态支持
============================================================
数据库类型: mysql

检测当前 status 字段的 ENUM 值...
   当前 ENUM 值: pending, running, completed, error, cancelled

开始更新 ENUM 定义...
   添加 'paused' 状态到 ENUM...
✅ ENUM 定义更新成功
✅ 验证成功：当前 ENUM 值包含 'paused'
   当前 ENUM 值: pending, running, paused, completed, error, cancelled
```

---

### 方法二：手动执行 SQL

如果迁移脚本无法执行，可以手动执行 SQL 语句。

#### MySQL 版本

**方式一：直接修改 ENUM（推荐，适用于 MySQL 5.7+）**

```sql
ALTER TABLE dedup_tasks 
MODIFY COLUMN status ENUM('pending', 'running', 'paused', 'completed', 'error', 'cancelled') 
NOT NULL DEFAULT 'pending' 
COMMENT '任务状态';
```

**方式二：两步法（如果方式一失败）**

```sql
-- 步骤 1: 将 status 字段转换为 VARCHAR
ALTER TABLE dedup_tasks 
MODIFY COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending' 
COMMENT '任务状态';

-- 步骤 2: 将 status 字段转换回 ENUM（包含 paused）
ALTER TABLE dedup_tasks 
MODIFY COLUMN status ENUM('pending', 'running', 'paused', 'completed', 'error', 'cancelled') 
NOT NULL DEFAULT 'pending' 
COMMENT '任务状态';
```

#### SQLite 版本

SQLite 使用 VARCHAR 类型，**无需修改表结构**。只需要确保代码中支持 `'paused'` 状态即可（代码已支持）。

#### PostgreSQL 版本

PostgreSQL 通常使用 VARCHAR 类型，**无需修改表结构**。只需要确保代码中支持 `'paused'` 状态即可（代码已支持）。

---

## 🔍 验证更新

### MySQL

```sql
-- 查看表结构
DESCRIBE dedup_tasks;

-- 查看 ENUM 值
SELECT COLUMN_TYPE 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME = 'dedup_tasks' 
  AND COLUMN_NAME = 'status';

-- 测试插入 paused 状态
UPDATE dedup_tasks SET status = 'paused' WHERE id = 1;
SELECT id, status FROM dedup_tasks WHERE id = 1;
```

### SQLite

```sql
-- 查看表结构
.schema dedup_tasks

-- 测试插入 paused 状态
UPDATE dedup_tasks SET status = 'paused' WHERE id = 1;
SELECT id, status FROM dedup_tasks WHERE id = 1;
```

---

## 📝 状态值说明

更新后的 `status` 字段支持以下状态值：

| 状态 | 说明 | 可执行操作 |
|------|------|-----------|
| `pending` | 待启动 | 启动任务 |
| `running` | 运行中 | 暂停任务、取消任务 |
| `paused` | 已暂停 | 继续任务、取消任务 |
| `completed` | 已完成 | 查看结果、删除任务 |
| `error` | 执行错误 | 查看错误信息、删除任务 |
| `cancelled` | 已取消 | 删除任务 |

**状态流转图**：
```
pending → running → paused → running → completed
   ↓         ↓         ↓
   └─────────┴─────────┘
         error/cancelled
```

---

## ⚠️ 注意事项

1. **备份数据**
   - 执行迁移前，建议先备份数据库
   - MySQL: `mysqldump -u username -p database_name > backup.sql`
   - SQLite: `cp app.db app.db.backup`

2. **检查表是否存在**
   - 如果 `dedup_tasks` 表不存在，需要先创建表
   - 参考 `sql/create_question_dedup_tables.sql` 文件

3. **检查字段是否已更新**
   - 如果 `status` 字段已包含 `'paused'`，迁移脚本会自动跳过
   - 可以手动验证：`DESCRIBE dedup_tasks;`（MySQL）或 `.schema dedup_tasks`（SQLite）

4. **MySQL ENUM 修改限制**
   - MySQL 修改 ENUM 类型可能需要重建表
   - 如果表中有大量数据，修改可能需要一些时间
   - 如果直接修改失败，脚本会自动尝试两步法

5. **SQLite 和 PostgreSQL**
   - SQLite 和 PostgreSQL 使用 VARCHAR 类型，无需修改表结构
   - 只需要确保代码中支持 `'paused'` 状态（代码已支持）

---

## 🚀 快速执行

### 使用修复脚本（推荐，最简单）

```bash
# 在项目根目录执行
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
python scripts/database/fix_paused_status.py

# Linux/Mac:
source venv/bin/activate
python scripts/database/fix_paused_status.py
```

### 验证修复结果

```bash
python scripts/database/verify_paused_status.py
```

### 使用迁移脚本（备选）

```bash
python scripts/database/migrate_add_paused_status.py
```

### 使用 SQL 文件

```bash
# MySQL
mysql -u username -p database_name < sql/add_paused_status_to_dedup_tasks.sql

# SQLite（通常不需要）
sqlite3 app.db < sql/add_paused_status_to_dedup_tasks.sql
```

---

## 📚 相关文件

- **修复脚本（推荐）**: `scripts/database/fix_paused_status.py`
- **验证脚本**: `scripts/database/verify_paused_status.py`
- **迁移脚本**: `scripts/database/migrate_add_paused_status.py`
- **SQL 文件**: `sql/add_paused_status_to_dedup_tasks.sql`
- **创建表 SQL**: `sql/create_question_dedup_tables.sql`
- **数据模型**: `src/models/question_dedup.py`
- **API 文档**: `docs/api/任务暂停和继续接口文档.md`

---

## ✅ 完成检查清单

- [ ] 执行修复脚本：`python scripts/database/fix_paused_status.py`
- [ ] 验证修复结果：`python scripts/database/verify_paused_status.py`
- [ ] 测试暂停任务功能
- [ ] 测试继续任务功能
- [ ] 确认 WebSocket 通知正常工作

---

**文档版本**: v1.0  
**最后更新**: 2024-01-05  
**维护人员**: 开发团队

