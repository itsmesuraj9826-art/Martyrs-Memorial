-- ============================================================
-- seed_board_members.sql
-- Run this once in MySQL Workbench to add the default faculty
-- members so they appear in both the Admin panel and About page.
-- Safe to re-run — uses INSERT IGNORE.
-- ============================================================

USE school_website;

INSERT IGNORE INTO board_members
  (name, position, category, bio, photo, email, phone, is_published, sort_order, created_at, updated_at)
VALUES
  (
    'CM Shrestha',
    'Principal',
    'faculty',
    'Leading Martyrs'' Memorial +2 with a vision for academic excellence and holistic student development.',
    NULL, NULL, NULL,
    1, 1,
    NOW(), NOW()
  ),
  (
    'Manish Adhikari',
    'HOD — Chemistry',
    'faculty',
    'Guiding students through the fascinating world of chemistry with practical and conceptual clarity.',
    NULL, NULL, NULL,
    1, 2,
    NOW(), NOW()
  );

-- Verify
SELECT id, name, position, category, is_published, sort_order FROM board_members ORDER BY sort_order;
