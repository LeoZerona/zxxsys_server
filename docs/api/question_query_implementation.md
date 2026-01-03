# 题目查询接口实现说明

## 概述

本文档说明题目查询类接口的实现情况。根据 `question_bank_api_spec.md` 文档，已完成题目查询类接口的实现。

## 文件结构

### 1. 数据模型层 (`src/models/question.py`)

定义了所有题目相关的数据模型：

- `Question`: 题目主表模型
- `SingleChoiceAnswer`: 单选题答案表
- `SingleChoiceOption`: 单选题选项表
- `MultChoiceAnswer`: 多选题答案表
- `MultChoiceOption`: 多选题选项表
- `JudgmentAnswer`: 判断题答案表
- `BlankAnswer`: 填空题答案表
- `CalcParentAnswer`: 计算分析题答案表（大题）
- `CalcChildAnswer`: 计算分析题子题答案表
- `CalcChildItem`: 计算分析题子题选项表
- `BlankChildAnswer`: 填空题答案子表（关联计算分析大题）

### 2. 聚合服务层 (`src/services/question_aggregation_service.py`)

负责将题目主表、答案表、选项表的数据聚合组装成统一的 JSON 结构：

- `aggregate_question()`: 聚合单个题目的完整数据
- `batch_aggregate_questions()`: 批量聚合题目数据（优化性能）
- 各题型的私有聚合方法：
  - `_aggregate_single_choice()`: 单选题聚合
  - `_aggregate_mult_choice()`: 多选题聚合
  - `_aggregate_judgment()`: 判断题聚合
  - `_aggregate_blank()`: 填空题聚合
  - `_aggregate_calc_analysis()`: 计算分析题聚合

### 3. 查询服务层 (`src/services/question_service.py`)

负责题目查询的业务逻辑：

- `get_question_list()`: 获取题目列表（分页）
- `get_question_detail()`: 获取单个题目详情
- `batch_get_questions()`: 批量获取题目详情
- `get_statistics()`: 获取题目统计信息

### 4. 路由层 (`src/routes/question.py`)

定义 API 路由和处理请求：

- `GET /api/questions`: 获取题目列表（分页）
- `GET /api/questions/<question_id>`: 获取单个题目详情
- `POST /api/questions/batch`: 批量获取题目详情
- `GET /api/questions/statistics`: 获取题目统计信息

## 已实现的接口

### 1. 获取题目列表接口

**接口地址**: `GET /api/questions`

**功能**: 按题型、渠道、科目等条件分页查询题目列表，返回聚合后的题目+答案+选项数据

**请求参数**:
- `type` (必填): 题型（1=单选, 2=多选, 3=判断, 4=填空, 8=计算分析）
- `channel_code` (可选): 渠道代码
- `subject_id` (可选): 科目 ID
- `subject_name` (可选): 科目名称
- `chapter_id` (可选): 章节 ID
- `attr` (可选): 题目属性
- `page` (可选): 页码，默认 1
- `page_size` (可选): 每页数量，默认 20，最大 100
- `include_answer` (可选): 是否包含答案，默认 true
- `include_analysis` (可选): 是否包含解析，默认 true

**响应格式**: 包含题目列表和分页信息

### 2. 获取单个题目详情接口

**接口地址**: `GET /api/questions/{question_id}`

**功能**: 根据题目 ID 获取完整的题目信息（包括题干、答案、选项、解析等）

**路径参数**:
- `question_id` (必填): 题目 ID

**请求参数**:
- `include_answer` (可选): 是否包含答案，默认 true
- `include_analysis` (可选): 是否包含解析，默认 true

**响应格式**: 单个题目的完整数据

### 3. 批量获取题目接口

**接口地址**: `POST /api/questions/batch`

**功能**: 根据题目 ID 列表批量获取题目详情

**请求体**:
```json
{
  "question_ids": [12345, 12346, 12347],
  "include_answer": true,
  "include_analysis": true
}
```

**响应格式**: 包含题目列表和未找到的ID列表

### 4. 题目统计接口

**接口地址**: `GET /api/questions/statistics`

**功能**: 获取题目统计信息

**请求参数**:
- `channel_code` (可选): 渠道代码
- `group_by` (可选): 分组方式（type/subject/channel）

**响应格式**: 包含总数和统计信息

## 特性

1. **分层架构**: 严格按照路由层、服务层、模型层分离
2. **批量查询优化**: 使用批量查询减少数据库往返次数
3. **数据聚合**: 自动将题目、答案、选项聚合为统一格式
4. **多题型支持**: 支持单选题、多选题、判断题、填空题、计算分析题
5. **软删除过滤**: 自动过滤已删除的题目（is_del=1）
6. **错误处理**: 完善的错误处理和错误码定义
7. **参数验证**: 严格的参数验证和类型检查

## 使用示例

### 获取单选题列表

```bash
GET /api/questions?type=1&page=1&page_size=20&channel_code=default
```

### 获取题目详情

```bash
GET /api/questions/12345?include_answer=true&include_analysis=true
```

### 批量获取题目

```bash
POST /api/questions/batch
Content-Type: application/json

{
  "question_ids": [12345, 12346, 12347],
  "include_answer": true,
  "include_analysis": true
}
```

### 获取统计信息

```bash
GET /api/questions/statistics?group_by=type&channel_code=default
```

## 注意事项

1. 所有接口都支持软删除过滤（is_del=0）
2. 批量查询接口限制最多100个题目ID
3. 分页查询每页最多100条
4. 计算分析题的结构较复杂，包含子题和选项
5. 不同渠道的题目需要分别处理

## 后续优化方向

1. 实现缓存策略（Redis）
2. 添加数据库索引优化
3. 实现请求限流
4. 添加接口监控和日志
5. 优化大批量查询性能

