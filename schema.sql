-- ============================================================
-- schema.sql — Clean MySQL 8+ compatible schema
-- No deprecated INT display widths, no warnings
-- Run: mysql -u root -p < schema.sql
-- Or paste into MySQL Workbench and Execute All (Ctrl+Shift+Enter)
-- ============================================================

CREATE DATABASE IF NOT EXISTS school_website
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE school_website;

-- ── Admins ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS admins (
    id                 INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    username           VARCHAR(80)  NOT NULL UNIQUE,
    email              VARCHAR(120) NOT NULL UNIQUE,
    password_hash      VARCHAR(255) NOT NULL,
    full_name          VARCHAR(150) NOT NULL,
    is_active          BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login         DATETIME,
    reset_token        VARCHAR(100),
    reset_token_expiry DATETIME,
    INDEX idx_admins_username (username),
    INDEX idx_admins_email    (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Notices ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS notices (
    id           INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(255) NOT NULL,
    content      TEXT         NOT NULL,
    category     VARCHAR(50)  NOT NULL DEFAULT 'general',
    is_pinned    BOOLEAN      NOT NULL DEFAULT FALSE,
    is_published BOOLEAN      NOT NULL DEFAULT TRUE,
    attachment   VARCHAR(255),
    expiry_date  DATE,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_notices_created          (created_at),
    INDEX idx_notices_published_pinned (is_published, is_pinned)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Events ────────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS events (
    id           INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(255) NOT NULL,
    description  TEXT         NOT NULL,
    location     VARCHAR(255),
    event_date   DATETIME     NOT NULL,
    end_date     DATETIME,
    banner_image VARCHAR(255),
    is_published BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_events_date      (event_date),
    INDEX idx_events_published (is_published)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Gallery Albums ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gallery_albums (
    id           INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(150) NOT NULL,
    description  TEXT,
    cover_image  VARCHAR(255),
    is_published BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Gallery Images ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gallery_images (
    id         INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    album_id   INT          NOT NULL,
    filename   VARCHAR(255) NOT NULL,
    caption    VARCHAR(255),
    sort_order INT          NOT NULL DEFAULT 0,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_gallery_images_album (album_id),
    CONSTRAINT fk_gallery_images_album
        FOREIGN KEY (album_id) REFERENCES gallery_albums (id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Blog Posts ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS blog_posts (
    id             INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title          VARCHAR(255) NOT NULL,
    slug           VARCHAR(255) NOT NULL UNIQUE,
    content        LONGTEXT     NOT NULL,
    excerpt        TEXT,
    featured_image VARCHAR(255),
    category       VARCHAR(80)  NOT NULL DEFAULT 'news',
    is_published   BOOLEAN      NOT NULL DEFAULT TRUE,
    is_featured    BOOLEAN      NOT NULL DEFAULT FALSE,
    views          INT          NOT NULL DEFAULT 0,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_blog_slug      (slug),
    INDEX idx_blog_created   (created_at),
    INDEX idx_blog_published (is_published)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Contact Messages ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS contact_messages (
    id         INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(150) NOT NULL,
    email      VARCHAR(150) NOT NULL,
    phone      VARCHAR(20),
    subject    VARCHAR(255) NOT NULL,
    message    TEXT         NOT NULL,
    is_read    BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_contact_created (created_at),
    INDEX idx_contact_read    (is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Downloads ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS downloads (
    id             INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title          VARCHAR(255) NOT NULL,
    description    TEXT,
    filename       VARCHAR(255) NOT NULL,
    original_name  VARCHAR(255) NOT NULL,
    category       VARCHAR(80)  NOT NULL DEFAULT 'general',
    file_size      INT,
    download_count INT          NOT NULL DEFAULT 0,
    is_published   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_downloads_category  (category),
    INDEX idx_downloads_published (is_published)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Homepage Content ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS homepage_content (
    id         INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    section    VARCHAR(80)  NOT NULL UNIQUE,
    title      VARCHAR(255),
    subtitle   VARCHAR(255),
    content    TEXT,
    image      VARCHAR(255),
    extra_data JSON,
    updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Testimonials ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS testimonials (
    id           INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(150) NOT NULL,
    role         VARCHAR(150),
    content      TEXT         NOT NULL,
    avatar       VARCHAR(255),
    rating       TINYINT      NOT NULL DEFAULT 5,
    is_published BOOLEAN      NOT NULL DEFAULT TRUE,
    sort_order   INT          NOT NULL DEFAULT 0,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Slides (homepage slideshow) ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS slides (
    id          INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(255) NULL,
    subtitle    VARCHAR(255) NULL,
    image       VARCHAR(255) NOT NULL,
    btn_text    VARCHAR(80)  NULL DEFAULT 'Learn More',
    btn_url     VARCHAR(255) NULL,
    sort_order  INT          NOT NULL DEFAULT 0,
    is_active   TINYINT(1)   NOT NULL DEFAULT 1,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Board Members ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS board_members (
    id           INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(150) NOT NULL,
    position     VARCHAR(150) NOT NULL,
    category     VARCHAR(80)  NOT NULL DEFAULT 'board',
    bio          TEXT,
    photo        VARCHAR(255),
    email        VARCHAR(120),
    phone        VARCHAR(30),
    is_published BOOLEAN      NOT NULL DEFAULT TRUE,
    sort_order   INT          NOT NULL DEFAULT 0,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_board_category   (category),
    INDEX idx_board_published  (is_published),
    INDEX idx_board_sort       (sort_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── Safe column additions (upgrade-safe, idempotent) ─────────────────────────
DROP PROCEDURE IF EXISTS add_column_if_not_exists;

DELIMITER $$
CREATE PROCEDURE add_column_if_not_exists(
    IN p_table      VARCHAR(64),
    IN p_column     VARCHAR(64),
    IN p_definition TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM   information_schema.COLUMNS
        WHERE  TABLE_SCHEMA = DATABASE()
          AND  TABLE_NAME   = p_table
          AND  COLUMN_NAME  = p_column
    ) THEN
        SET @sql = CONCAT(
            'ALTER TABLE `', p_table,
            '` ADD COLUMN `', p_column, '` ', p_definition
        );
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$
DELIMITER ;

CALL add_column_if_not_exists('admins', 'reset_token',        'VARCHAR(100)');
CALL add_column_if_not_exists('admins', 'reset_token_expiry', 'DATETIME');

DROP PROCEDURE IF EXISTS add_column_if_not_exists;

-- ── Default Admin Account ─────────────────────────────────────────────────────
-- Email   : surajmehta9826@gmail.com
-- Password: suraj@123  (hashed with Werkzeug scrypt — matches Flask app)
-- Safe to re-run: ON DUPLICATE KEY UPDATE resets password if needed.
INSERT INTO admins
    (username, email, password_hash, full_name, is_active)
VALUES (
    'surajmehta',
    'surajmehta9826@gmail.com',
    'scrypt:32768:8:1$YSQi0S7yzaSEIQsW$410b7053b8302dc28e5181bcc2fda2cbfde19ff99c688c413f531188a47f28739fafa14650f0a319ca1f1269441a7ed3758e8f088139691e61e1f3b637a23cda',
    'Suraj Mehta',
    TRUE
)
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    full_name     = VALUES(full_name),
    is_active     = TRUE;

-- ── Done ──────────────────────────────────────────────────────────────────────
SELECT 'Schema ready — admin account seeded, no warnings!' AS status;
