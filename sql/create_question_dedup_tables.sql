-- ============================================================================
-- 题目去重相关表创建 SQL 语句
-- ============================================================================
-- 说明：用于存储题目去重的任务记录、重复结果和特征数据
-- 支持多次去重操作，保留历史记录
-- ============================================================================

-- ============================================================================
-- MySQL 版本
-- ============================================================================

-- 1. 去重任务表（记录每次去重任务的元信息）
CREATE TABLE IF NOT EXISTS dedup_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '任务ID',
    task_name VARCHAR(200) COMMENT '任务名称（可选）',
    status ENUM('pending', 'running', 'paused', 'completed', 'error', 'cancelled') NOT NULL DEFAULT 'pending' COMMENT '任务状态',
    total_groups INT DEFAULT 0 COMMENT '总分组数',
    processed_groups INT DEFAULT 0 COMMENT '已处理分组数',
    total_questions INT DEFAULT 0 COMMENT '总题目数',
    exact_duplicate_groups INT DEFAULT 0 COMMENT '完全重复组数',
    exact_duplicate_pairs INT DEFAULT 0 COMMENT '完全重复对数',
    similar_duplicate_pairs INT DEFAULT 0 COMMENT '相似重复对数',
    started_at DATETIME COMMENT '开始时间',
    completed_at DATETIME COMMENT '完成时间',
    error_message TEXT COMMENT '错误信息',
    config_json TEXT COMMENT '任务配置（JSON格式）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='去重任务表';

-- 2. 重复题目对表（记录重复的题目对，包括完全重复和相似重复）
CREATE TABLE IF NOT EXISTS question_duplicate_pairs (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    task_id INT NOT NULL COMMENT '任务ID',
    question_id_1 INT NOT NULL COMMENT '题目ID 1',
    question_id_2 INT NOT NULL COMMENT '题目ID 2',
    similarity DECIMAL(5,4) NOT NULL COMMENT '相似度 (0-1)',
    duplicate_type ENUM('exact', 'similar') NOT NULL COMMENT '重复类型：exact=完全重复, similar=相似重复',
    group_type VARCHAR(2) COMMENT '题型',
    group_subject_id INT COMMENT '科目ID',
    group_channel_code VARCHAR(20) COMMENT '渠道代码',
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '检测时间',
    INDEX idx_task_id (task_id),
    INDEX idx_question_1 (question_id_1),
    INDEX idx_question_2 (question_id_2),
    INDEX idx_similarity (similarity),
    INDEX idx_type (duplicate_type),
    INDEX idx_group (group_type, group_subject_id, group_channel_code),
    UNIQUE KEY uk_task_pair (task_id, question_id_1, question_id_2),
    FOREIGN KEY (task_id) REFERENCES dedup_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='重复题目对表';

-- 3. 完全重复题目组表（记录一组完全相同的题目）
CREATE TABLE IF NOT EXISTS question_duplicate_groups (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '组ID',
    task_id INT NOT NULL COMMENT '任务ID',
    content_hash VARCHAR(32) NOT NULL COMMENT '内容哈希值（MD5）',
    question_count INT NOT NULL COMMENT '题目数量',
    group_type VARCHAR(2) COMMENT '题型',
    group_subject_id INT COMMENT '科目ID',
    group_channel_code VARCHAR(20) COMMENT '渠道代码',
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '检测时间',
    INDEX idx_task_id (task_id),
    INDEX idx_content_hash (content_hash),
    INDEX idx_group (group_type, group_subject_id, group_channel_code),
    FOREIGN KEY (task_id) REFERENCES dedup_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='完全重复题目组表';

-- 4. 完全重复组明细表（记录组内每个题目的详细信息）
CREATE TABLE IF NOT EXISTS question_duplicate_group_items (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    group_id INT NOT NULL COMMENT '组ID',
    task_id INT NOT NULL COMMENT '任务ID',
    question_id INT NOT NULL COMMENT '题目ID',
    INDEX idx_group_id (group_id),
    INDEX idx_task_id (task_id),
    INDEX idx_question_id (question_id),
    UNIQUE KEY uk_group_question (group_id, question_id),
    FOREIGN KEY (group_id) REFERENCES question_duplicate_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES dedup_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='完全重复组明细表';

-- 5. 题目去重特征表（记录题目的特征数据，用于分析和优化）
CREATE TABLE IF NOT EXISTS question_dedup_features (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    task_id INT NOT NULL COMMENT '任务ID',
    question_id INT NOT NULL COMMENT '题目ID',
    cleaned_content TEXT COMMENT '清洗后的题目内容',
    content_hash VARCHAR(32) COMMENT '内容哈希值（MD5）',
    ngram_json TEXT COMMENT 'N-gram特征（JSON数组格式）',
    minhash_json TEXT COMMENT 'MinHash指纹（JSON数组格式，128个整数）',
    group_type VARCHAR(2) COMMENT '题型',
    group_subject_id INT COMMENT '科目ID',
    group_channel_code VARCHAR(20) COMMENT '渠道代码',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_task_id (task_id),
    INDEX idx_question_id (question_id),
    INDEX idx_content_hash (content_hash),
    INDEX idx_group (group_type, group_subject_id, group_channel_code),
    UNIQUE KEY uk_task_question (task_id, question_id),
    FOREIGN KEY (task_id) REFERENCES dedup_tasks(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='题目去重特征表';

-- ============================================================================
-- SQLite 版本（如果需要）
-- ============================================================================

/*
-- 1. 去重任务表
CREATE TABLE IF NOT EXISTS dedup_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name VARCHAR(200),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    total_groups INTEGER DEFAULT 0,
    processed_groups INTEGER DEFAULT 0,
    total_questions INTEGER DEFAULT 0,
    exact_duplicate_groups INTEGER DEFAULT 0,
    exact_duplicate_pairs INTEGER DEFAULT 0,
    similar_duplicate_pairs INTEGER DEFAULT 0,
    started_at DATETIME,
    completed_at DATETIME,
    error_message TEXT,
    config_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dedup_tasks_status ON dedup_tasks(status);
CREATE INDEX IF NOT EXISTS idx_dedup_tasks_created_at ON dedup_tasks(created_at);

-- 2. 重复题目对表
CREATE TABLE IF NOT EXISTS question_duplicate_pairs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    question_id_1 INTEGER NOT NULL,
    question_id_2 INTEGER NOT NULL,
    similarity REAL NOT NULL,
    duplicate_type VARCHAR(10) NOT NULL,
    group_type VARCHAR(2),
    group_subject_id INTEGER,
    group_channel_code VARCHAR(20),
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES dedup_tasks(id) ON DELETE CASCADE,
    UNIQUE(task_id, question_id_1, question_id_2)
);

CREATE INDEX IF NOT EXISTS idx_dup_pairs_task_id ON question_duplicate_pairs(task_id);
CREATE INDEX IF NOT EXISTS idx_dup_pairs_question_1 ON question_duplicate_pairs(question_id_1);
CREATE INDEX IF NOT EXISTS idx_dup_pairs_question_2 ON question_duplicate_pairs(question_id_2);
CREATE INDEX IF NOT EXISTS idx_dup_pairs_similarity ON question_duplicate_pairs(similarity);

-- 3. 完全重复题目组表
CREATE TABLE IF NOT EXISTS question_duplicate_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    content_hash VARCHAR(32) NOT NULL,
    question_count INTEGER NOT NULL,
    group_type VARCHAR(2),
    group_subject_id INTEGER,
    group_channel_code VARCHAR(20),
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES dedup_tasks(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_dup_groups_task_id ON question_duplicate_groups(task_id);
CREATE INDEX IF NOT EXISTS idx_dup_groups_content_hash ON question_duplicate_groups(content_hash);

-- 4. 完全重复组明细表
CREATE TABLE IF NOT EXISTS question_duplicate_group_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    FOREIGN KEY (group_id) REFERENCES question_duplicate_groups(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES dedup_tasks(id) ON DELETE CASCADE,
    UNIQUE(group_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_dup_group_items_group_id ON question_duplicate_group_items(group_id);
CREATE INDEX IF NOT EXISTS idx_dup_group_items_question_id ON question_duplicate_group_items(question_id);

-- 5. 题目去重特征表
CREATE TABLE IF NOT EXISTS question_dedup_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    cleaned_content TEXT,
    content_hash VARCHAR(32),
    ngram_json TEXT,
    minhash_json TEXT,
    group_type VARCHAR(2),
    group_subject_id INTEGER,
    group_channel_code VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES dedup_tasks(id) ON DELETE CASCADE,
    UNIQUE(task_id, question_id)
);

CREATE INDEX IF NOT EXISTS idx_dedup_features_task_id ON question_dedup_features(task_id);
CREATE INDEX IF NOT EXISTS idx_dedup_features_question_id ON question_dedup_features(question_id);
*/

