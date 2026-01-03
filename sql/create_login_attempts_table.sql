-- 登录尝试记录表
-- 用于记录登录失败次数，防止暴力破解攻击

CREATE TABLE IF NOT EXISTS `login_attempts` (
  `id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  `email` VARCHAR(120) NOT NULL,
  `ip_address` VARCHAR(45) NULL,
  `attempt_count` INT NOT NULL DEFAULT 1,
  `first_attempt_at` DATETIME NOT NULL,
  `last_attempt_at` DATETIME NOT NULL,
  `requires_captcha` BOOLEAN NOT NULL DEFAULT FALSE,
  `captcha_verified` BOOLEAN NOT NULL DEFAULT FALSE,
  INDEX `idx_email` (`email`),
  INDEX `idx_ip_address` (`ip_address`),
  INDEX `idx_first_attempt_at` (`first_attempt_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- SQLite 版本（如果使用 SQLite）
-- CREATE TABLE IF NOT EXISTS `login_attempts` (
--   `id` INTEGER PRIMARY KEY AUTOINCREMENT,
--   `email` VARCHAR(120) NOT NULL,
--   `ip_address` VARCHAR(45),
--   `attempt_count` INTEGER NOT NULL DEFAULT 1,
--   `first_attempt_at` DATETIME NOT NULL,
--   `last_attempt_at` DATETIME NOT NULL,
--   `requires_captcha` BOOLEAN NOT NULL DEFAULT 0,
--   `captcha_verified` BOOLEAN NOT NULL DEFAULT 0
-- );
-- 
-- CREATE INDEX IF NOT EXISTS `idx_email` ON `login_attempts` (`email`);
-- CREATE INDEX IF NOT EXISTS `idx_ip_address` ON `login_attempts` (`ip_address`);
-- CREATE INDEX IF NOT EXISTS `idx_first_attempt_at` ON `login_attempts` (`first_attempt_at`);

