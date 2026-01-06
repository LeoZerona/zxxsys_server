-- ============================================================================
-- 为去重任务表添加 'paused' 状态
-- ============================================================================
-- 说明：此 SQL 用于更新 dedup_tasks 表的 status 字段，添加 'paused' 状态支持
-- 执行时间：在部署暂停/继续功能之前执行
-- ============================================================================

-- MySQL 版本
-- 注意：MySQL 的 ENUM 类型修改需要重建表或使用 ALTER TABLE MODIFY
-- 如果表中有数据，建议先备份

-- 方式一：使用 ALTER TABLE MODIFY（推荐，适用于 MySQL 5.7+）
ALTER TABLE dedup_tasks 
MODIFY COLUMN status ENUM('pending', 'running', 'paused', 'completed', 'error', 'cancelled') 
NOT NULL DEFAULT 'pending' 
COMMENT '任务状态';

-- 方式二：如果方式一失败，可以尝试先删除枚举约束，再重新添加
-- ALTER TABLE dedup_tasks 
-- MODIFY COLUMN status VARCHAR(20) NOT NULL DEFAULT 'pending';
-- 
-- ALTER TABLE dedup_tasks 
-- MODIFY COLUMN status ENUM('pending', 'running', 'paused', 'completed', 'error', 'cancelled') 
-- NOT NULL DEFAULT 'pending' 
-- COMMENT '任务状态';

-- SQLite 版本（SQLite 不支持 ENUM，使用 VARCHAR）
-- 如果使用 SQLite，status 字段已经是 VARCHAR 类型，无需修改
-- 只需要确保代码中支持 'paused' 状态即可

-- 验证修改是否成功
-- SELECT COLUMN_TYPE FROM INFORMATION_SCHEMA.COLUMNS 
-- WHERE TABLE_SCHEMA = DATABASE() 
-- AND TABLE_NAME = 'dedup_tasks' 
-- AND COLUMN_NAME = 'status';

