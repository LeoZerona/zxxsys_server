-- ============================================================================
-- 数据库迁移脚本：为 dedup_tasks 表添加新字段
-- ============================================================================
-- 说明：添加 analysis_type（分析类型）和 estimated_duration（预估时长）字段
-- 执行时间：2024-01-XX
-- ============================================================================

-- ============================================================================
-- MySQL 版本
-- ============================================================================

-- 检查字段是否存在，如果不存在则添加
-- 注意：MySQL 不支持 IF NOT EXISTS，需要手动检查或使用存储过程

-- 添加 analysis_type 字段（分析类型）
ALTER TABLE dedup_tasks 
ADD COLUMN IF NOT EXISTS analysis_type VARCHAR(50) DEFAULT 'full' 
COMMENT '分析类型：full=全量分析, incremental=增量分析, custom=自定义分析' 
AFTER config_json;

-- 添加 estimated_duration 字段（预估时长，单位：秒）
ALTER TABLE dedup_tasks 
ADD COLUMN IF NOT EXISTS estimated_duration INT 
COMMENT '预估时长（秒）' 
AFTER analysis_type;

-- 如果 MySQL 版本不支持 IF NOT EXISTS，可以使用以下方式：
-- 先检查字段是否存在，如果不存在再添加
-- 或者直接执行 ALTER TABLE，如果字段已存在会报错，可以忽略

-- ============================================================================
-- SQLite 版本（如果需要）
-- ============================================================================

/*
-- SQLite 不支持 ALTER TABLE ADD COLUMN IF NOT EXISTS
-- 需要先检查字段是否存在，然后添加

-- 添加 analysis_type 字段
ALTER TABLE dedup_tasks 
ADD COLUMN analysis_type VARCHAR(50) DEFAULT 'full';

-- 添加 estimated_duration 字段
ALTER TABLE dedup_tasks 
ADD COLUMN estimated_duration INTEGER;
*/

-- ============================================================================
-- 验证脚本（可选）
-- ============================================================================

-- 验证字段是否添加成功
-- SELECT COLUMN_NAME, DATA_TYPE, COLUMN_DEFAULT, COLUMN_COMMENT
-- FROM INFORMATION_SCHEMA.COLUMNS
-- WHERE TABLE_SCHEMA = DATABASE()
--   AND TABLE_NAME = 'dedup_tasks'
--   AND COLUMN_NAME IN ('analysis_type', 'estimated_duration');

