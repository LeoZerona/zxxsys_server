# 题库接口功能设计文档（方案 A）

本文档基于方案 A（API 层聚合 + 批量查询 + 缓存）设计，详细描述题库相关接口的功能分类、接口规范、数据聚合策略等。

## 一、功能分类

### 1.1 题目查询类接口

#### 1.1.1 获取题目列表（分页）

- **功能描述**：按题型、渠道、科目等条件分页查询题目列表，返回聚合后的题目+答案+选项数据
- **使用场景**：题库浏览、题目筛选、分页加载

#### 1.1.2 获取单个题目详情

- **功能描述**：根据题目 ID 获取完整的题目信息（包括题干、答案、选项、解析等）
- **使用场景**：题目详情页、错题回顾、题目编辑

#### 1.1.3 批量获取题目

- **功能描述**：根据题目 ID 列表批量获取题目详情
- **使用场景**：练习册加载、错题本、收藏夹批量展示

### 1.2 题目筛选类接口

#### 1.2.1 按题型筛选

- **功能描述**：根据题型（单选、多选、判断、填空、计算分析）筛选题目
- **使用场景**：题型练习、专项训练

#### 1.2.2 按科目筛选

- **功能描述**：根据科目 ID 或科目名称筛选题目
- **使用场景**：科目专项练习、科目分类浏览

#### 1.2.3 按章节筛选

- **功能描述**：根据章节 ID 筛选题目

- **使用场景**：章节练习、按章节学习

#### 1.2.4 组合筛选

- **功能描述**：支持多条件组合筛选（题型+科目+章节+渠道+属性等）
- **使用场景**：精准练习、自定义练习

### 1.3 统计类接口

#### 1.3.1 题目统计信息

- **功能描述**：获取各题型、各科目的题目数量统计
- **使用场景**：题库概览、数据统计面板

#### 1.3.2 渠道题目统计

- **功能描述**：按渠道统计题目数量
- **使用场景**：渠道管理、数据报表

## 二、接口详细设计

### 2.1 获取题目列表接口

**接口地址**: `GET /api/questions`

**接口描述**: 分页获取题目列表，返回聚合后的完整题目数据（题目+答案+选项）

**请求参数**:

| 参数名           | 类型    | 必填 | 说明                                                       | 示例值    |
| ---------------- | ------- | ---- | ---------------------------------------------------------- | --------- |
| type             | string  | 是   | 题型：`1`=单选, `2`=多选, `3`=判断, `4`=填空, `8`=计算分析 | `1`       |
| channel_code     | string  | 否   | 渠道代码，默认查询所有渠道                                 | `default` |
| subject_id       | int     | 否   | 科目 ID                                                    | `1`       |
| subject_name     | string  | 否   | 科目名称                                                   | `会计学`  |
| chapter_id       | int     | 否   | 章节 ID                                                    | `10`      |
| attr             | string  | 否   | 题目属性                                                   | `01`      |
| page             | int     | 否   | 页码，默认 1                                               | `1`       |
| page_size        | int     | 否   | 每页数量，默认 20，最大 100                                | `20`      |
| include_answer   | boolean | 否   | 是否包含答案，默认 true                                    | `true`    |
| include_analysis | boolean | 否   | 是否包含解析，默认 true                                    | `true`    |

**请求示例**:

```
GET /api/questions?type=1&channel_code=default&page=1&page_size=20
```

**响应格式**:

```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "list": [
      {
        "question_id": 12345,
        "type": "1",
        "type_name": "单选题",
        "subject_id": 1,
        "subject_name": "会计学",
        "chapter_id": 10,
        "subject_type": "01",
        "subject_type_name": "财务会计",
        "content": "题目内容...",
        "content_detail": "题目简要",
        "analysis": "题目解析...",
        "attr": "01",
        "sort": 0,
        "channel_code": "default",
        "create_time": "2024-01-01T00:00:00",
        "answer": {
          "correct_answer": "A",
          "option_true": "A"
        },
        "options": [
          {
            "label": "A",
            "content": "选项A内容",
            "seq": 1
          },
          {
            "label": "B",
            "content": "选项B内容",
            "seq": 2
          }
        ]
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 49226,
      "total_pages": 2462
    }
  }
}
```

**不同题型的响应结构差异**:

- **单选题 (type=1)**: `answer.correct_answer` 为单个选项标签，`options` 为选项数组
- **多选题 (type=2)**: `answer.correct_answer` 为数组（如 `["A","B"]`），`options` 为选项数组
- **判断题 (type=3)**: `answer.correct_answer` 为 `1`（正确）或 `2`（错误），无 `options`
- **填空题 (type=4)**: `answer.correct_answer` 为答案文本，无 `options`
- **计算分析题 (type=8)**: `answer` 包含 `sub_questions` 数组，每个子题有自己的答案和选项

**错误响应**:

- 400: 参数错误

```json
{
  "success": false,
  "message": "题型参数无效，支持的类型：1,2,3,4,8"
}
```

- 500: 服务器错误

```json
{
  "success": false,
  "message": "服务器内部错误"
}
```

### 2.2 获取单个题目详情接口

**接口地址**: `GET /api/questions/{question_id}`

**接口描述**: 根据题目 ID 获取完整的题目详情

**路径参数**:

| 参数名      | 类型 | 必填 | 说明    |
| ----------- | ---- | ---- | ------- |
| question_id | int  | 是   | 题目 ID |

**请求参数**:

| 参数名           | 类型    | 必填 | 说明                    |
| ---------------- | ------- | ---- | ----------------------- |
| include_answer   | boolean | 否   | 是否包含答案，默认 true |
| include_analysis | boolean | 否   | 是否包含解析，默认 true |

**请求示例**:

```
GET /api/questions/12345?include_answer=true&include_analysis=true
```

**响应格式**: 同题目列表中的单个题目对象结构

**错误响应**:

- 404: 题目不存在

```json
{
  "success": false,
  "message": "题目不存在或已被删除"
}
```

### 2.3 批量获取题目接口

**接口地址**: `POST /api/questions/batch`

**接口描述**: 根据题目 ID 列表批量获取题目详情

**请求体**:

```json
{
  "question_ids": [12345, 12346, 12347],
  "include_answer": true,
  "include_analysis": true
}
```

**请求参数**:

| 参数名           | 类型       | 必填 | 说明                      |
| ---------------- | ---------- | ---- | ------------------------- |
| question_ids     | array[int] | 是   | 题目 ID 数组，最多 100 个 |
| include_answer   | boolean    | 否   | 是否包含答案，默认 true   |
| include_analysis | boolean    | 否   | 是否包含解析，默认 true   |

**响应格式**:

```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "questions": [
      // 题目对象数组，同单个题目详情结构
    ],
    "not_found_ids": [12350] // 未找到的题目ID
  }
}
```

**错误响应**:

- 400: 参数错误

```json
{
  "success": false,
  "message": "题目ID列表不能为空，且最多100个"
}
```

### 2.4 题目统计接口

**接口地址**: `GET /api/questions/statistics`

**接口描述**: 获取题目统计信息

**请求参数**:

| 参数名       | 类型   | 必填 | 说明                                                        |
| ------------ | ------ | ---- | ----------------------------------------------------------- |
| channel_code | string | 否   | 渠道代码，不传则统计所有渠道                                |
| group_by     | string | 否   | 分组方式：`type`=按题型, `subject`=按科目, `channel`=按渠道 |

**请求示例**:

```
GET /api/questions/statistics?group_by=type&channel_code=default
```

**响应格式**:

```json
{
  "success": true,
  "message": "获取成功",
  "data": {
    "total": 91149,
    "statistics": [
      {
        "type": "1",
        "type_name": "单选题",
        "count": 49226
      },
      {
        "type": "2",
        "type_name": "多选题",
        "count": 11134
      },
      {
        "type": "3",
        "type_name": "判断题",
        "count": 2059
      },
      {
        "type": "4",
        "type_name": "填空题",
        "count": 17671
      },
      {
        "type": "8",
        "type_name": "计算分析题",
        "count": 1059
      }
    ]
  }
}
```

## 三、数据聚合策略

### 3.1 查询流程

1. **查询题目主表**

   - 从 `teach_question` 表查询题目基础信息
   - 根据题型 `type` 过滤
   - 应用筛选条件（渠道、科目、章节等）
   - 过滤软删除记录（`is_del = 0`）
   - 分页处理

2. **批量查询答案表**

   - 根据题型和题目 ID 列表，批量查询对应的答案表：
     - 单选题：`teach_ans_single_choice`
     - 多选题：`teach_ans_mult_choice`
     - 判断题：`teach_ans_judgment`
     - 填空题：`teach_ans_blank`
     - 计算分析题：`teach_ans_calcparent`

3. **批量查询选项/子表**

   - 对于有选项的题型，批量查询选项子表：
     - 单选题选项：`teach_ans_single_choice_child`
     - 多选题选项：`teach_ans_mult_choice_child`
     - 计算分析题子题：`teach_ans_calcchild`
     - 计算分析题子题选项：`teach_ans_calcchild_item`（如子题为不定项选择题）
     - 计算分析题填空子题：`teach_ans_blankchild`

4. **内存聚合组装**
   - 在应用层将题目、答案、选项按 ID 关联
   - 组装成统一的 JSON 结构
   - 处理缺失数据（题目无对应答案时返回提示）

### 3.2 题型映射关系

| 题型代码 | 题型名称   | 题目表           | 答案表                    | 选项/子表                                                                   |
| -------- | ---------- | ---------------- | ------------------------- | --------------------------------------------------------------------------- |
| 1        | 单选题     | `teach_question` | `teach_ans_single_choice` | `teach_ans_single_choice_child`                                             |
| 2        | 多选题     | `teach_question` | `teach_ans_mult_choice`   | `teach_ans_mult_choice_child`                                               |
| 3        | 判断题     | `teach_question` | `teach_ans_judgment`      | 无                                                                          |
| 4        | 填空题     | `teach_question` | `teach_ans_blank`         | 无（或 `teach_ans_blankchild` 当关联计算大题时）                            |
| 8        | 计算分析题 | `teach_question` | `teach_ans_calcparent`    | `teach_ans_calcchild` + `teach_ans_calcchild_item` / `teach_ans_blankchild` |

### 3.3 ID 对应关系约定

- **单选题**: `question_id = singlechoice_id`
- **多选题**: `question_id = multchoice_id`
- **判断题**: `question_id = judgment_id`
- **填空题**: `question_id = blank_id`
- **计算分析题**: `question_id = calcparent_id`

### 3.4 数据校验

- 查询答案表时，校验题目 ID 是否存在对应答案（防止孤儿数据）
- 查询选项子表时，校验答案 ID 是否存在对应选项
- 对于缺失答案的题目，在响应中标记或过滤
- 统一过滤软删除记录（`is_del = 0`）

## 四、缓存策略

### 4.1 缓存层级

#### 4.1.1 列表缓存（粗粒度）

- **缓存 Key**: `question:list:{type}:{channel_code}:{subject_id}:{chapter_id}:{page}:{page_size}`
- **缓存内容**: 题目 ID 列表
- **缓存时间**: 5-10 分钟
- **失效策略**: 题目新增/更新/删除时，清除相关列表缓存

#### 4.1.2 题目详情缓存（细粒度）

- **缓存 Key**: `question:detail:{question_id}`
- **缓存内容**: 完整的聚合后题目对象（JSON）
- **缓存时间**: 30 分钟
- **失效策略**: 题目更新时清除对应题目缓存

#### 4.1.3 统计信息缓存

- **缓存 Key**: `question:statistics:{channel_code}:{group_by}`
- **缓存内容**: 统计结果
- **缓存时间**: 1 小时
- **失效策略**: 题目新增/删除时清除统计缓存

### 4.2 缓存实现建议

- 使用 Redis 作为缓存存储
- 缓存键统一前缀：`question:`
- 实现缓存穿透保护（空结果也缓存，时间较短）
- 实现缓存击穿保护（使用互斥锁）
- 批量查询时，优先从缓存获取，缓存未命中再批量查询数据库

### 4.3 缓存更新策略

- **写操作触发**：题目新增/更新/删除时，清除相关缓存
- **主动刷新**：定时任务每小时刷新统计缓存
- **手动刷新**：提供管理接口手动清除指定缓存

## 五、索引优化建议

### 5.1 题目表索引

```sql
-- 主要查询索引：渠道+题型+软删+排序
CREATE INDEX idx_question_channel_type_del_sort
ON teach_question(channel_code, type, is_del, sort);

-- 科目筛选索引
CREATE INDEX idx_question_channel_subject_del
ON teach_question(channel_code, subject_id, is_del);

-- 章节筛选索引
CREATE INDEX idx_question_channel_chapter_del
ON teach_question(channel_code, chapter_id, is_del);

-- 复合筛选索引
CREATE INDEX idx_question_channel_type_subject_del
ON teach_question(channel_code, type, subject_id, is_del);
```

### 5.2 答案表索引

```sql
-- 单选题答案表：批量查询用
CREATE INDEX idx_single_choice_id ON teach_ans_single_choice(singlechoice_id);
-- 单选题选项表：外键索引
CREATE INDEX idx_single_choice_child_id ON teach_ans_single_choice_child(singlechoice_id);

-- 多选题答案表
CREATE INDEX idx_mult_choice_id ON teach_ans_mult_choice(multchoice_id);
-- 多选题选项表
CREATE INDEX idx_mult_choice_child_id ON teach_ans_mult_choice_child(multchoice_id);

-- 判断题答案表
CREATE INDEX idx_judgment_id ON teach_ans_judgment(judgment_id);

-- 填空题答案表
CREATE INDEX idx_blank_id ON teach_ans_blank(blank_id);

-- 计算分析题答案表
CREATE INDEX idx_calcparent_id ON teach_ans_calcparent(calcparent_id);
-- 计算分析题子题表
CREATE INDEX idx_calcchild_parent_id ON teach_ans_calcchild(calcparent_id);
-- 计算分析题子题选项表
CREATE INDEX idx_calcchild_item_id ON teach_ans_calcchild_item(calcchild_id);
-- 计算分析题填空子题表
CREATE INDEX idx_blankchild_parent_id ON teach_ans_blankchild(calcparent_id);
```

### 5.3 索引使用原则

- 优先使用组合索引覆盖常用查询条件
- 避免过度索引（影响写入性能）
- 定期分析慢查询，优化索引策略
- 为批量 IN 查询的字段建立索引

## 六、错误处理

### 6.1 错误码定义

| HTTP 状态码 | 错误码            | 说明               |
| ----------- | ----------------- | ------------------ |
| 200         | SUCCESS           | 请求成功           |
| 400         | INVALID_PARAMETER | 参数错误           |
| 401         | UNAUTHORIZED      | 未授权（如需登录） |
| 403         | FORBIDDEN         | 无权限             |
| 404         | NOT_FOUND         | 资源不存在         |
| 429         | TOO_MANY_REQUESTS | 请求过于频繁       |
| 500         | INTERNAL_ERROR    | 服务器内部错误     |

### 6.2 错误响应格式

```json
{
  "success": false,
  "error_code": "INVALID_PARAMETER",
  "message": "题型参数无效",
  "details": {
    "field": "type",
    "reason": "支持的类型：1,2,3,4,8"
  }
}
```

### 6.3 常见错误场景

1. **参数验证错误**

   - 题型参数无效
   - 分页参数超出范围
   - 题目 ID 列表为空或超限

2. **数据不存在**

   - 题目不存在
   - 题目已被删除
   - 题目无对应答案

3. **权限错误**

   - 未登录（如需要）
   - 无访问权限

4. **系统错误**
   - 数据库连接失败
   - 缓存服务异常
   - 内部逻辑错误

## 七、性能优化建议

### 7.1 查询优化

- 使用批量查询减少数据库往返次数
- 限制单次查询的题目数量（最多 100 条）
- 分页查询时使用 LIMIT/OFFSET 或游标分页
- 避免 N+1 查询问题

### 7.2 响应优化

- 支持字段选择（只返回需要的字段，减少响应体积）
- 使用 JSON 压缩（gzip）
- 大文本字段（如 content、analysis）考虑按需返回
- 优化 JSON 序列化性能

### 7.3 并发控制

- 实现请求限流（Rate Limiting），防止接口被滥用
- 对批量查询接口限制并发数
- 使用连接池管理数据库连接

### 7.4 数据预加载

- 热门题目预热到缓存
- 统计信息定时预计算
- 批量查询时优先从缓存读取

## 八、实现要点

### 8.1 数据聚合服务层设计

#### 8.1.1 服务类结构

- **QuestionService**: 题目查询服务

  - `get_question_list()`: 获取题目列表
  - `get_question_detail()`: 获取题目详情
  - `batch_get_questions()`: 批量获取题目

- **QuestionAggregationService**: 题目聚合服务

  - `aggregate_single_choice()`: 聚合单选题数据
  - `aggregate_mult_choice()`: 聚合多选题数据
  - `aggregate_judgment()`: 聚合判断题数据
  - `aggregate_blank()`: 聚合填空题数据
  - `aggregate_calc_analysis()`: 聚合计算分析题数据

- **QuestionCacheService**: 题目缓存服务
  - `get_cached_list()`: 获取缓存的列表
  - `get_cached_detail()`: 获取缓存的详情
  - `invalidate_cache()`: 失效缓存

#### 8.1.2 数据模型

- **QuestionDTO**: 题目数据传输对象

  - 包含题目基础信息、答案、选项等聚合后的完整数据

- **QuestionListQuery**: 查询条件对象

  - 封装查询参数（题型、渠道、科目等）

- **PaginationResult**: 分页结果对象
  - 包含数据列表和分页信息

### 8.2 批量查询实现

#### 8.2.1 查询流程

```
1. 查询题目主表（teach_question）
   ↓
2. 提取题目ID列表
   ↓
3. 根据题型批量查询答案表（IN查询）
   ↓
4. 对于有选项的题型，批量查询选项子表（IN查询）
   ↓
5. 在内存中按ID关联组装数据
   ↓
6. 返回聚合后的JSON结果
```

#### 8.2.2 SQL 示例

**批量查询单选题答案**:

```sql
SELECT * FROM teach_ans_single_choice
WHERE singlechoice_id IN (?, ?, ?, ...)
AND channel_code = ?
```

**批量查询单选题选项**:

```sql
SELECT * FROM teach_ans_single_choice_child
WHERE singlechoice_id IN (?, ?, ?, ...)
AND channel_code = ?
ORDER BY singlechoice_id, seq
```

### 8.3 缓存实现

#### 8.3.1 缓存结构

- **列表缓存**: 存储查询条件对应的题目 ID 列表
- **详情缓存**: 存储完整的聚合后题目对象（JSON 字符串）

#### 8.3.2 缓存更新策略

- **新增题目**: 清除相关列表缓存和统计缓存
- **更新题目**: 清除题目详情缓存和相关列表缓存
- **删除题目**: 清除题目详情缓存、相关列表缓存和统计缓存

### 8.4 异常处理

- **数据缺失处理**: 题目无对应答案时，记录日志并返回提示信息
- **孤儿数据处理**: 答案表中存在题目表中不存在的记录，跳过处理
- **缓存失效处理**: 缓存服务异常时，降级到直接查询数据库

## 九、测试建议

### 9.1 单元测试

- 测试各题型的聚合逻辑
- 测试批量查询功能
- 测试缓存读写逻辑
- 测试数据校验逻辑

### 9.2 集成测试

- 测试完整查询流程（数据库查询 → 聚合 → 返回）
- 测试缓存命中/未命中场景
- 测试不同题型的接口响应

### 9.3 性能测试

- 测试批量查询性能（100 条、500 条、1000 条）
- 测试缓存命中率
- 测试并发查询性能
- 测试数据库查询响应时间

### 9.4 数据一致性测试

- 验证题目与答案的关联正确性
- 验证选项顺序正确性
- 验证软删除过滤正确性

## 十、后续优化方向

### 10.1 短期优化（1-3 个月）

- 完善缓存策略，提高缓存命中率
- 优化数据库查询，减少查询时间
- 添加更多索引，提升查询性能
- 实现请求限流，保护接口

### 10.2 中期优化（3-6 个月）

- 考虑引入物化聚合表（方案 C）
- 实现题目搜索功能（全文检索）
- 优化大批量查询性能（游标分页）
- 实现接口监控和告警

### 10.3 长期优化（6 个月以上）

- 考虑引入搜索引擎（如 Elasticsearch）支持复杂查询
- 实现读写分离，提升查询性能
- 考虑微服务拆分，独立题库服务
- 实现题目推荐功能

## 附录

### A. 题型代码说明

| 题型代码 | 题型名称   | 说明                     |
| -------- | ---------- | ------------------------ |
| 1        | 单选题     | 只有一个正确答案         |
| 2        | 多选题     | 有多个正确答案           |
| 3        | 判断题     | 正确或错误               |
| 4        | 填空题     | 填写答案                 |
| 8        | 计算分析题 | 包含多个子题的综合性题目 |

### B. 题目属性（attr）说明

- 题目属性字段用于标记题目的特殊属性（如难度、来源等）
- 具体值需要根据业务需求定义

### C. 渠道代码说明

- `channel_code` 用于区分不同的业务渠道或租户
- 查询时默认查询所有渠道，可指定渠道代码进行过滤

### D. 相关表结构参考

详细表结构说明请参考：`docs/test_db_schema.md`

---

**文档版本**: v1.0  
**最后更新**: 2024-01-01  
**维护人员**: 开发团队
