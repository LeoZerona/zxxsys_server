-- ============================================================================
-- 数据库迁移：为用户表添加权限字段
-- ============================================================================
-- 说明：如果users表已存在，执行此SQL添加role字段
-- ============================================================================

-- SQLite 版本
-- ============================================================================
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL;

-- 为现有用户设置默认权限（如果需要）
UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';

-- 创建索引（可选，提高查询性能）
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

-- ============================================================================
-- MySQL 版本
-- ============================================================================
/*
ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user' AFTER password_hash;
UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';
CREATE INDEX idx_users_role ON users(role);
*/

-- ============================================================================
-- PostgreSQL 版本
-- ============================================================================
/*
ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user';
UPDATE users SET role = 'user' WHERE role IS NULL OR role = '';
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
*/

-- ============================================================================
-- 字段说明
-- ============================================================================
/*
role 字段说明：
- 字段名: role
- 类型: VARCHAR(20)
- 默认值: 'user'
- 允许值:
  * 'super_admin' - 超级管理员（最高权限）
  * 'admin' - 管理员
  * 'user' - 普通用户（默认）
- 索引: 已创建，提高按权限查询的性能
*/

