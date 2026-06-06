USE school_website;

-- ── Hero section ──────────────────────────────────────────────────────────────
INSERT INTO homepage_content (section, title, subtitle, content)
VALUES ('hero',
        "Martyrs' Memorial +2",
        'Biratnagar-10, College Road',
        'A premier institution committed to holistic education, nurturing bright minds and building tomorrow\'s leaders in an inspiring environment.')
ON DUPLICATE KEY UPDATE
    title    = VALUES(title),
    subtitle = VALUES(subtitle),
    content  = VALUES(content);

-- ── About section ─────────────────────────────────────────────────────────────
INSERT INTO homepage_content (section, title, subtitle, content)
VALUES ('about',
        "A Legacy of Excellence",
        "Martyrs' Memorial +2",
        "Martyrs' Memorial +2, located at Biratnagar-10 on College Road, is one of the region's leading higher secondary institutions. Offering +2 programmes in Science, Computer Science, Management and Hotel Management, we have shaped thousands of students into confident, capable individuals ready for the challenges of tomorrow.")
ON DUPLICATE KEY UPDATE
    title   = VALUES(title),
    content = VALUES(content);

-- ── Principal section ─────────────────────────────────────────────────────────
INSERT INTO homepage_content (section, title, subtitle, content)
VALUES ('principal',
        "Principal's Message",
        'CM Shrestha, Principal',
        "Education is not merely the acquisition of knowledge — it is the cultivation of character, curiosity, and compassion. At Martyrs' Memorial +2, every student is valued, challenged, and inspired to reach their highest potential. We are committed to providing an environment where academic excellence and personal growth go hand in hand.")
ON DUPLICATE KEY UPDATE
    title    = VALUES(title),
    subtitle = VALUES(subtitle),
    content  = VALUES(content);

-- ── Mission section ───────────────────────────────────────────────────────────
INSERT INTO homepage_content (section, title, subtitle, content)
VALUES ('mission',
        'To provide holistic, quality education that nurtures intellectual curiosity, ethical values, and leadership skills in every student.',
        'To be a regionally recognized institution that empowers students to become responsible citizens and lifelong learners.',
        'Integrity, Respect, Excellence, Innovation, Inclusivity — the pillars that guide every decision and interaction in our community.')
ON DUPLICATE KEY UPDATE
    title    = VALUES(title),
    subtitle = VALUES(subtitle),
    content  = VALUES(content);

SELECT section, title, subtitle FROM homepage_content;
