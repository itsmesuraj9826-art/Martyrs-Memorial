-- ============================================================
-- migrate_slides_popup.sql
-- Run once in MySQL Workbench to add new tables/data
-- Safe to re-run
-- ============================================================

USE school_website;

-- ── 1. Slides table ──────────────────────────────────────────
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

-- ── 2. Seed the admission popup (disabled by default) ────────
INSERT INTO homepage_content (section, title, subtitle, content, extra_data, updated_at)
VALUES (
  'popup',
  'Admissions Now Open',
  '2025 – 26',
  'We are pleased to announce that admissions are open for the academic year 2025–26. Join one of our prestigious +2 programmes — Science, Management, Law, or Arts — and take the first step towards a bright future.',
  JSON_OBJECT('enabled', FALSE),
  NOW()
)
ON DUPLICATE KEY UPDATE updated_at = updated_at;  -- don't overwrite if already exists

-- Verify
SELECT 'slides table' AS item, COUNT(*) AS rows FROM slides
UNION ALL
SELECT 'popup content', COUNT(*) FROM homepage_content WHERE section = 'popup';
