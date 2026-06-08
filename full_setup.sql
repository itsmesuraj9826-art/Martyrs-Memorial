-- ============================================================
-- full_setup.sql — Complete School Website Database Setup
-- Run this ONCE in MySQL Workbench (Ctrl+Shift+Enter)
-- Safe to re-run — uses IF NOT EXISTS & ON DUPLICATE KEY
-- ============================================================

-- ── 1. Create & select database ──────────────────────────────
CREATE DATABASE IF NOT EXISTS school_website
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE school_website;

-- ── 2. Admins ─────────────────────────────────────────────────
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

-- ── 3. Notices ────────────────────────────────────────────────
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

-- ── 4. Events ─────────────────────────────────────────────────
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

-- ── 5. Gallery Albums ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS gallery_albums (
    id           INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(150) NOT NULL,
    description  TEXT,
    cover_image  VARCHAR(255),
    is_published BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 6. Gallery Images ─────────────────────────────────────────
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

-- ── 7. Blog Posts ─────────────────────────────────────────────
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

-- ── 8. Contact Messages ───────────────────────────────────────
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

-- ── 9. Downloads ──────────────────────────────────────────────
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

-- ── 10. Homepage Content ──────────────────────────────────────
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

-- ── 11. Testimonials ──────────────────────────────────────────
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

-- ── 12. Board Members ─────────────────────────────────────────
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
    updated_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 13. Toppers ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS toppers (
    id           INT           NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(150)  NOT NULL,
    stream       VARCHAR(50)   NOT NULL,
    percentage   DECIMAL(5,2)  NULL,
    year         VARCHAR(10)   NOT NULL DEFAULT '2024',
    photo        VARCHAR(255)  NULL,
    rank         INT           NOT NULL DEFAULT 1,
    is_published TINYINT(1)    NOT NULL DEFAULT 1,
    sort_order   INT           NOT NULL DEFAULT 0,
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_toppers_stream     (stream),
    INDEX idx_toppers_published  (is_published)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 14. Slides (homepage slideshow) ──────────────────────────
CREATE TABLE IF NOT EXISTS slides (
    id          INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(255),
    subtitle    VARCHAR(255),
    image       VARCHAR(255) NOT NULL,
    btn_text    VARCHAR(80)           DEFAULT 'Learn More',
    btn_url     VARCHAR(255),
    sort_order  INT          NOT NULL DEFAULT 0,
    is_active   TINYINT(1)   NOT NULL DEFAULT 1,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ── 14. Safe column additions (upgrade-safe) ─────────────────
DROP PROCEDURE IF EXISTS add_col;
DELIMITER $$
CREATE PROCEDURE add_col(
    IN p_table  VARCHAR(64),
    IN p_column VARCHAR(64),
    IN p_def    TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME   = p_table
          AND COLUMN_NAME  = p_column
    ) THEN
        SET @sql = CONCAT('ALTER TABLE `', p_table, '` ADD COLUMN `', p_column, '` ', p_def);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$
DELIMITER ;

CALL add_col('admins',           'reset_token',        'VARCHAR(100)');
CALL add_col('admins',           'reset_token_expiry', 'DATETIME');
CALL add_col('contact_messages', 'stream',             'VARCHAR(80) NULL');

DROP PROCEDURE IF EXISTS add_col;

-- ── 15. Default admin account ─────────────────────────────────
-- Login : username = msuraj24   OR   email = msuraj24@tbc.edu.np
-- Password: suraj@123
INSERT INTO admins (username, email, password_hash, full_name, is_active)
VALUES (
    'msuraj24',
    'msuraj24@tbc.edu.np',
    'scrypt:32768:8:1$YSQi0S7yzaSEIQsW$410b7053b8302dc28e5181bcc2fda2cbfde19ff99c688c413f531188a47f28739fafa14650f0a319ca1f1269441a7ed3758e8f088139691e61e1f3b637a23cda',
    'Suraj Mehta',
    TRUE
)
ON DUPLICATE KEY UPDATE
    username      = 'msuraj24',
    email         = 'msuraj24@tbc.edu.np',
    password_hash = VALUES(password_hash),
    full_name     = 'Suraj Mehta',
    is_active     = TRUE;

-- Remove old surajmehta account if it exists
DELETE FROM admins WHERE username = 'surajmehta' AND email = 'surajmehta9826@gmail.com';

-- ── 16. Seed homepage content ─────────────────────────────────
INSERT INTO homepage_content (section, title, subtitle, content, extra_data)
VALUES
  ('hero',
   'Welcome to Martyrs'' Memorial +2',
   'Biratnagar-10, College Road',
   'A premier institution committed to holistic education, nurturing bright minds and building tomorrow''s leaders in an inspiring environment.',
   NULL),
  ('about',
   'A Legacy of Excellence',
   NULL,
   'Martyrs'' Memorial +2, located at Biratnagar-10 on College Road, is one of the region''s leading higher secondary institutions affiliated to the National Examination Board (NEB). Offering +2 programmes in Science, Management, Law, and Arts, we have shaped thousands of students into confident, capable individuals ready for the challenges of tomorrow.',
   NULL),
  ('principal',
   'Principal''s Message',
   'CM Shrestha, Principal',
   'Education is not just the filling of a pail, but the lighting of a fire. At Martyrs'' Memorial +2, we are committed to igniting that spark in every student — empowering them with knowledge, character, and the confidence to face tomorrow''s challenges.',
   NULL),
  ('mission',
   'To provide holistic, quality education that nurtures intellectual curiosity, ethical values, and leadership skills in every student.',
   'To be a regionally recognized institution that empowers students to become responsible citizens and lifelong learners.',
   'Integrity, Respect, Excellence, Innovation, Inclusivity — the pillars that guide every decision and interaction in our community.',
   NULL),
  ('popup',
   'Admissions Now Open',
   '2025 – 26',
   'We are pleased to announce that admissions are open for the academic year 2025–26. Join one of our prestigious +2 programmes — Science, Management, Law, or Arts — and take the first step towards a bright future.',
   JSON_OBJECT('enabled', FALSE))
ON DUPLICATE KEY UPDATE updated_at = updated_at;

-- ── 17. Seed default board/faculty members ────────────────────
INSERT IGNORE INTO board_members
  (name, position, category, bio, is_published, sort_order)
VALUES
  ('CM Shrestha',    'Principal',       'faculty',
   'Leading Martyrs'' Memorial +2 with a vision for academic excellence and holistic student development.',
   TRUE, 1),
  ('Manish Adhikari','HOD — Chemistry', 'faculty',
   'Guiding students through the fascinating world of chemistry with practical and conceptual clarity.',
   TRUE, 2);

-- ── 18. Verification ──────────────────────────────────────────
SELECT 'admins'           AS tbl, COUNT(*) AS total FROM admins
UNION ALL
SELECT 'homepage_content',         COUNT(*) FROM homepage_content
UNION ALL
SELECT 'board_members',            COUNT(*) FROM board_members
UNION ALL
SELECT 'slides',                   COUNT(*) FROM slides;

SELECT '✅ Setup complete! Login with: msuraj24 / suraj@123' AS status;
