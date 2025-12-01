# 测试文档

## 测试概述

本项目包含完整的单元测试，覆盖以下功能模块：

1. **数据库连接和模型测试** (`test_database.py`)
   - 数据库初始化
   - 数据库连接
   - 用户模型操作
   - 邮箱验证码模型操作

2. **邮箱服务测试** (`test_email_service.py`)
   - 验证码生成
   - 验证码发送
   - 验证码验证
   - 过期处理

3. **API 接口测试** (`test_api.py`)
   - 健康检查
   - 用户注册
   - 发送验证码
   - 验证验证码
   - 获取用户信息

## 运行测试

### 安装测试依赖

```bash
pip install -r requirements.txt
```

### 运行所有测试

```bash
pytest
```

### 运行特定测试文件

```bash
# 测试数据库
pytest tests/test_database.py

# 测试邮箱服务
pytest tests/test_email_service.py

# 测试 API
pytest tests/test_api.py
```

### 运行特定测试类

```bash
pytest tests/test_database.py::TestDatabaseConnection
```

### 运行特定测试方法

```bash
pytest tests/test_database.py::TestDatabaseConnection::test_database_initialization
```

### 查看详细输出

```bash
pytest -v
```

### 查看覆盖率

```bash
pytest --cov=. --cov-report=html
```

## 测试配置

测试使用临时 SQLite 数据库，每个测试运行前会自动创建，运行后自动清理。测试配置在 `conftest.py` 中定义。

## 测试数据

- 测试邮箱：`test@example.com`
- 测试密码：`test123456`

## 注意事项

1. 邮箱服务在测试模式下不会发送真实邮件，验证码会打印到控制台
2. 每个测试使用独立的数据库实例，互不干扰
3. 测试会自动清理临时数据

