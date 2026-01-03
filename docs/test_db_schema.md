## test 数据库结构说明

本文基于当前本地 MySQL 实例（默认端口、用户 `root`）的 `test` 库实勘结果整理，包含表/视图字段含义、用途以及推测的关联关系，便于前后端对齐和后续扩展。

### 总览
- 表：`users`、`email_verifications`、`login_attempts`、`refresh_tokens`、`teach_question`、`teach_ans_*` 系列（题目答案与解析）、`teach_ans_*_child` 系列（子题/选项）、`teach_ans_calcchild_item`、`teach_ans_calcparent`。
- 视图：`single_choice_question`（从 `teach_question` 过滤单选题）。
- 唯一明确的外键：`refresh_tokens.user_id → users.id`。其他业务关联需由代码约定（如题目 ID 对应各答案表的主键）。

### 关系梳理
- 认证域
  - `users` 一对多 `refresh_tokens`（持久化刷新令牌）。
  - `email_verifications` 与 `login_attempts` 通过 `email`（及可选 `ip_address`）逻辑关联用户，但未设置外键。
- 题库/练习域
  - `teach_question` 为题目主表；`single_choice_question` 视图筛选 `type` LIKE '%1%' 的单选题。
  - 题目答案按题型拆分：单选 `teach_ans_single_choice` + 子选项表， 多选 `teach_ans_mult_choice` + 子选项表， 判断 `teach_ans_judgment`， 填空 `teach_ans_blank`（及其子表）， 计算/分析题用 `teach_ans_calcparent`（大题）+ `teach_ans_calcchild`（小题）+ `teach_ans_calcchild_item`（不定项选项）。
  - `calcparent` 与 `calcchild`/`blankchild` 通过 `calcparent_id` 形成 1:N；`calcchild` 与 `calcchild_item` 通过 `calcchild_id` 形成 1:N；`*_child` 表与对应主表通过各自的 `*_id` 形成 1:N。
  - 题目与答案表未建外键，通常通过“题目 ID = 各答案表主键”或渠道 `channel_code` 在应用侧约定。
- 多租/渠道：绝大多数题库相关表包含 `channel_code`，用于区分渠道或租户。
- 软删除：题库表普遍有 `is_del` 软删除标记（0 正常，1 删除）。

### 表/视图字段明细

#### users（用户）
用途：系统用户与权限基础。

| 字段 | 类型 | 允许空 | 默认 | 键 | 说明 |
| --- | --- | --- | --- | --- | --- |
| id | int | 否 |  | PK | 自增主键 |
| email | varchar(120) | 否 |  | UNIQUE, IDX | 登录邮箱 |
| password_hash | varchar(255) | 否 |  |  | 密码哈希 |
| role | varchar(20) | 否 |  | IDX | 角色标识 |
| created_at | datetime | 是 |  |  | 创建时间 |
| updated_at | datetime | 是 |  |  | 更新时间 |
| is_active | tinyint(1) | 是 |  |  | 启用状态 |

关联：一对多 `refresh_tokens.user_id`。

#### email_verifications（邮箱验证码）
用途：邮箱验证/找回密码验证码存储。

| 字段 | 类型 | 允许空 | 默认 | 键 | 说明 |
| --- | --- | --- | --- | --- | --- |
| id | int | 否 |  | PK | 自增主键 |
| email | varchar(120) | 否 |  | IDX | 目标邮箱 |
| code | varchar(10) | 否 |  |  | 验证码 |
| is_used | tinyint(1) | 否 |  |  | 是否已使用 |
| created_at | datetime | 是 |  |  | 创建时间 |
| expires_at | datetime | 否 |  |  | 过期时间 |

关联：按 `email` 逻辑关联用户，无外键。

#### login_attempts（登录尝试）
用途：记录登录失败次数、首末尝试时间及是否需要验证码。

| 字段 | 类型 | 允许空 | 默认 | 键 | 说明 |
| --- | --- | --- | --- | --- | --- |
| id | int | 否 |  | PK | 自增主键 |
| email | varchar(120) | 否 |  | IDX | 登录邮箱 |
| ip_address | varchar(45) | 是 |  | IDX | 来源 IP |
| attempt_count | int | 否 |  |  | 尝试次数 |
| first_attempt_at | datetime | 否 |  |  | 首次尝试时间 |
| last_attempt_at | datetime | 否 |  |  | 最近尝试时间 |
| requires_captcha | tinyint(1) | 否 |  |  | 是否需验证码 |
| captcha_verified | tinyint(1) | 否 |  |  | 验证码是否通过 |

关联：按 `email`/`ip_address` 逻辑关联用户，无外键。

#### refresh_tokens（刷新令牌）
用途：持久化刷新令牌，用于长登录会话。

| 字段 | 类型 | 允许空 | 默认 | 键 | 说明 |
| --- | --- | --- | --- | --- | --- |
| id | int | 否 |  | PK | 自增主键 |
| user_id | int | 否 |  | FK | 关联用户 |
| token_hash | varchar(255) | 否 |  | UNIQUE | 令牌哈希 |
| is_revoked | tinyint(1) | 否 |  |  | 是否吊销 |
| expires_at | datetime | 否 |  |  | 过期时间 |
| created_at | datetime | 是 |  |  | 创建时间 |
| last_used_at | datetime | 是 |  |  | 最近使用时间 |
| user_agent | varchar(255) | 是 |  |  | UA |
| ip_address | varchar(45) | 是 |  |  | IP |

关联：`user_id → users.id`（唯一外键）。

#### teach_question（考试题目）
用途：题目主表，存储题干、类型、科目等。

| 字段 | 类型 | 允许空 | 默认 | 键 | 说明 |
| --- | --- | --- | --- | --- | --- |
| question_id | int | 否 |  | PK | 自增主键 |
| subject_id | int | 是 |  |  | 科目 ID |
| subject_name | varchar(50) | 是 |  |  | 科目名称 |
| chapter_id | int | 是 |  |  | 章节 ID |
| subject_type | varchar(50) | 是 |  |  | 科目类型 |
| subject_type_name | varchar(50) | 是 |  | IDX | 科目类型名 |
| content | mediumtext | 是 |  |  | 题目内容 |
| content_detail | char(100) | 是 |  |  | 题目内容简要 |
| type | char(2) | 是 |  | IDX | 题型（如 1=单选） |
| analysis | longtext | 是 |  |  | 题目解析 |
| attr | char(2) | 是 |  | IDX | 题目属性 |
| sort | int | 是 | 0 |  | 排序 |
| remark | varchar(100) | 是 |  |  | 备注 |
| channel_code | char(20) | 否 |  | IDX | 渠道 |
| create_time | timestamp | 是 |  |  | 创建时间 |
| is_del | int | 是 | 0 |  | 软删标记（1 删除） |

关联：被 `single_choice_question` 视图引用；题目 ID 通常与各题型答案表的主键对应（无外键约束）。

#### single_choice_question（视图：单选题）
定义：`teach_question` 中 `type` LIKE '%1%' 的题目集合。
字段：同 `teach_question`。
用途：方便按单选题类型查询。

#### teach_ans_single_choice（单选题答案）

| 字段 | 类型 | 允许空 | 默认 | 键 | 说明 |
| --- | --- | --- | --- | --- | --- |
| singlechoice_id | int | 否 |  | PK | 单选题主键（对应题目） |
| option_true | varchar(200) | 是 |  |  | 正确选项 |
| channel_code | char(20) | 否 |  | IDX | 渠道 |

子表：`teach_ans_single_choice_child`（选项列表）。

#### teach_ans_single_choice_child（单选题答案子表）

| 字段 | 类型 | 允许空 | 默认 | 键 | 说明 |
| --- | --- | --- | --- | --- | --- |
| singlechoice_child_id | int | 否 |  | PK | 自增 |
| singlechoice_id | int | 否 |  | IDX | 选择题主键 |
| option_content | varchar(512) | 是 |  |  | 精确答案 |
| label | varchar(2) | 是 |  |  | 选项标签 |
| seq | int | 是 |  |  | 排序 |
| channel_code | char(20) | 否 |  | IDX | 渠道 |

关系：`singlechoice_id` 逻辑关联 `teach_ans_single_choice.singlechoice_id`（无外键）。

#### teach_ans_mult_choice（多选题答案）

| 字段 | 类型 | 允许空 | 默认 | 键 | 说明 |
| --- | --- | --- | --- | --- | --- |
| multchoice_id | int | 否 |  | PK | 自增/主键 |
| option_true | varchar(200) | 是 |  |  | 正确选项集合 |
| channel_code | char(20) | 否 |  | IDX | 渠道 |

子表：`teach_ans_mult_choice_child`。

#### teach_ans_mult_choice_child（多选题答案子表）

| 字段 | 类型 | 允许空 | 默认 | 键 | 说明 |
| --- | --- | --- | --- | --- | --- |
| multchoice_child_id | int | 否 |  | PK | 自增 |
| multchoice_id | int | 是 |  | IDX | 多选题主键 |
| option_content | varchar(512) | 是 |  |  | 选项内容 |
| label | varchar(2) | 是 |  |  | 选项标签 |
| seq | int | 是 |  |  | 排序 |
| channel_code | char(20) | 否 |  | IDX | 渠道 |

#### teach_ans_judgment（判断题答案）

| 字段 | 类型 | 允许空 | 默认 | 键 | 说明 |
| --- | --- | --- | --- | --- | --- |
| judgment_id | int | 否 |  | PK | 主键 |
| option_true | char(1) | 是 |  |  | 正确选项标识（1/2 等） |
| channel_code | char(20) | 否 |  | IDX | 渠道 |

#### teach_ans_blank（填空题答案）

| 字段 | 类型 | 允许空 | 默认 | 键 | 说明 |
| --- | --- | --- | --- | --- | --- |
| blank_id | int | 否 |  | PK | 自增主键 |
| answer_content | mediumtext | 是 |  |  | 答案内容 |
| channel_code | char(20) | 否 |  | IDX | 渠道 |
| create_time | timestamp | 是 |  |  | 创建时间 |
| is_del | int | 是 | 0 |  | 软删 |

子表：`teach_ans_blankchild`（关联计算分析大题）。

#### teach_ans_blankchild（填空题答案子表）

| 字段 | 类型 | 允许空 | 默认 | 键 | 说明 |
| --- | --- | --- | --- | --- | --- |
| blankchild_id | int | 否 |  | PK | 自增 |
| calcparent_id | int | 否 |  | IDX | 计算分析大题主键 |
| type | char(2) | 是 |  |  | 小题分类：4=填空题 |
| content | varchar(1000) | 是 |  |  | 题目内容 |
| answer_content | varchar(8000) | 是 |  |  | 答案 |
| analysis | varchar(8000) | 是 |  |  | 解析 |
| sort | int | 是 | 0 |  | 排序 |
| channel_code | char(20) | 否 |  | IDX | 渠道 |
| create_time | timestamp | 是 |  |  | 创建时间 |
| is_del | int | 是 | 0 |  | 软删 |

关系：`calcparent_id` 逻辑关联 `teach_ans_calcparent.calcparent_id`。

#### teach_ans_calcparent（计算分析大题）

| 字段 | 类型 | 允许空 | 默认 | 键 | 说明 |
| --- | --- | --- | --- | --- | --- |
| calcparent_id | int | 否 |  | PK | 主键（大题） |
| type2 | char(2) | 否 | 0 |  | 1=分录题 2=填空题 |
| channel_code | char(20) | 否 |  | IDX | 渠道 |

子表：`teach_ans_calcchild`（小题），`teach_ans_blankchild`（填空型小题）。

#### teach_ans_calcchild（计算分析小题）

| 字段 | 类型 | 允许空 | 默认 | 键 | 说明 |
| --- | --- | --- | --- | --- | --- |
| calcchild_id | int | 否 |  | PK | 自增主键 |
| calcparent_id | int | 否 |  | IDX | 对应大题 |
| type | char(2) | 是 |  |  | 1=分录题 2=填空题 3=不定项选择 |
| content | varchar(1000) | 是 |  |  | 题目内容 |
| answer_content | varchar(8000) | 是 |  |  | 答案 |
| analysis | varchar(5000) | 是 |  |  | 解析 |
| option_true | varchar(200) | 是 |  |  | 正确选项（用于选择类） |
| sort | int | 是 | 0 |  | 排序 |
| channel_code | char(20) | 否 |  | IDX | 渠道 |
| create_time | timestamp | 是 |  |  | 创建时间 |
| is_del | int | 是 | 0 |  | 软删 |

子表：`teach_ans_calcchild_item`。

#### teach_ans_calcchild_item（不定项选择题答案子表）

| 字段 | 类型 | 允许空 | 默认 | 键 | 说明 |
| --- | --- | --- | --- | --- | --- |
| calcchild_item_id | int | 否 |  | PK | 自增 |
| calcchild_id | int | 是 |  | IDX | 对应小题 |
| option_content | varchar(512) | 是 |  |  | 选项内容 |
| label | varchar(2) | 是 |  |  | 选项标签 |
| seq | int | 是 |  |  | 排序 |
| channel_code | char(20) | 否 |  | IDX | 渠道 |

关系：`calcchild_id` 逻辑关联 `teach_ans_calcchild.calcchild_id`。

#### teach_ans_blank（已列于上方）
见“填空题答案”段。

#### teach_ans_mult_choice / _child、teach_ans_single_choice / _child、teach_ans_judgment
见对应段落。

### 视图/表命名与题型映射（推测）
- `teach_question.type`：
  - 包含 `1`：单选题（对应视图 `single_choice_question`，答案表 `teach_ans_single_choice`）。
  - 其他类型可能对应：`teach_ans_mult_choice`（多选）、`teach_ans_judgment`（判断）、`teach_ans_blank`（填空）、`teach_ans_calcparent`+子表（计算/分录/综合题）。
- 实际映射需结合应用逻辑确认；目前数据库未以外键强制关联。

### 数据质量与建模建议
- 可考虑为题目与各答案表间补充外键，避免孤立记录，并加上统一的 `question_id` 字段而非复用主键名。
- `users` 及认证表建议补充创建/更新默认值和审计字段（如 `updated_at` 触发器）。
- 统一 `is_del` 的取值范围（0/1）和默认值，并为题库表添加必需索引（如 `channel_code` 已有，视需要加上 `subject_id` / `chapter_id`）。
- 避免在命令行明文传递密码，可改用 `~/.my.cnf` 或环境变量。

