# 配置 MySQL test 数据库

## 问题说明

当前应用默认使用的是 SQLite 数据库（`app.db`），但你需要使用 MySQL 的 `test` 数据库。

## 解决方法

### 方法一：创建 .env 文件（推荐）

创建 `.env` 文件在项目根目录：

```env
DATABASE_URL=mysql+pymysql://root:123456@localhost:3306/test?charset=utf8mb4
```

或者使用环境变量方式：

```env
MYSQL_USER=root
MYSQL_PASSWORD=123456
MYSQL_HOST=localhost
MYSQL_PORT=3306
```

### 方法二：直接修改 config.py（临时）

在 `config.py` 中已经修改为默认使用 MySQL，但如果你的 MySQL 密码不是 `123456`，需要：
1. 创建 `.env` 文件设置 `MYSQL_PASSWORD=你的密码`
2. 或者直接修改 `config.py` 中的默认密码

## 配置完成后

1. **重启 Flask 服务**（重要！）
2. 重新运行测试脚本验证

