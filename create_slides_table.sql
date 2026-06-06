-- Run this in MySQL Workbench if slides table doesn't exist yet
USE school_website;

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

SELECT 'slides table ready' AS status, COUNT(*) AS slide_count FROM slides;
