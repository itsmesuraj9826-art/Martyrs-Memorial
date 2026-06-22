"""
MySQL (school_website) → Render PostgreSQL (martyrs_db2)
=========================================================
Run this on YOUR PC with XAMPP MySQL running:
    cd C:/Users/ASUS/Desktop/fixed-school-website
    pip install pymysql psycopg2-binary sqlalchemy
    python migrate_to_new_db.py
"""
import sys
from sqlalchemy import create_engine, text, MetaData

MYSQL_URL = "mysql+pymysql://root:suraj%40123@localhost:3306/school_website?charset=utf8mb4"
PG_URL    = "postgresql://martyrs_db2_user:rVtdYixmOYaySPO45BtM6wrcguzYL3Zf@dpg-d8snbncm0tmc739e0n20-a.virginia-postgres.render.com/martyrs_db2"

# Parent tables first, then children
TABLE_ORDER = [
    "admins",
    "homepage_content",
    "notices",
    "events",
    "gallery_albums",
    "gallery_images",   # depends on gallery_albums
    "blog_posts",
    "contact_messages",
    "downloads",
    "testimonials",
    "board_members",
    "slides",
    "facilities",
]

print("Connecting to MySQL...")
mysql_engine = create_engine(MYSQL_URL)
try:
    with mysql_engine.connect() as c:
        c.execute(text("SELECT 1"))
    print("✅ MySQL connected (school_website)")
except Exception as e:
    print(f"❌ MySQL failed: {e}")
    print("   Make sure XAMPP is running!")
    sys.exit(1)

print("Connecting to Render PostgreSQL...")
pg_engine = create_engine(PG_URL)
try:
    with pg_engine.connect() as c:
        c.execute(text("SELECT 1"))
    print("✅ PostgreSQL connected (martyrs_db2)")
except Exception as e:
    print(f"❌ PostgreSQL failed: {e}")
    sys.exit(1)

mysql_meta = MetaData()
mysql_meta.reflect(bind=mysql_engine)
pg_meta = MetaData()
pg_meta.reflect(bind=pg_engine)

available_mysql = set(mysql_meta.tables.keys())
available_pg    = set(pg_meta.tables.keys())

print(f"\nMySQL tables : {sorted(available_mysql)}")
print(f"PG tables    : {sorted(available_pg)}\n")

for table_name in TABLE_ORDER:
    if table_name not in available_mysql:
        print(f"⚠  '{table_name}' — not in MySQL, skipping")
        continue
    if table_name not in available_pg:
        print(f"⚠  '{table_name}' — not in PostgreSQL, skipping")
        continue

    mysql_table = mysql_meta.tables[table_name]
    pg_table    = pg_meta.tables[table_name]

    with mysql_engine.connect() as mc:
        rows = [dict(r) for r in mc.execute(mysql_table.select()).mappings().all()]

    if not rows:
        print(f"   '{table_name}' — empty, skipping")
        continue

    with pg_engine.connect() as pc:
        pc.execute(pg_table.delete())
        pc.commit()
        for i in range(0, len(rows), 500):
            pc.execute(pg_table.insert(), rows[i:i+500])
        pc.commit()

    print(f"✅ '{table_name}' — {len(rows)} rows migrated")

print("\nResetting PostgreSQL sequences...")
with pg_engine.connect() as pc:
    for t in TABLE_ORDER:
        if t not in available_pg:
            continue
        try:
            pc.execute(text(
                f"SELECT setval(pg_get_serial_sequence('{t}','id'), "
                f"COALESCE((SELECT MAX(id) FROM {t}), 1))"
            ))
        except Exception:
            pass
    pc.commit()

print("\n🎉 Done! All data is now in Render PostgreSQL (martyrs_db2).")
