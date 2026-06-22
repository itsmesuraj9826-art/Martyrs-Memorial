"""
Upload all local static/uploads images to Cloudinary
and update the database records with new Cloudinary URLs.

Run ONCE on your PC:
    python upload_images_to_cloudinary.py
"""
import os, sys
from urllib.parse import urlparse

# ── Config ────────────────────────────────────────────────────────────────────
PG_URL         = "postgresql://martyrs_db2_user:rVtdYixmOYaySPO45BtM6wrcguzYL3Zf@dpg-d8snbncm0tmc739e0n20-a.virginia-postgres.render.com/martyrs_db2"
UPLOADS_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")

CLOUDINARY_URL = "cloudinary://989382454569146:DgBhqIKSjw5bUaOb6lfhsJwD3hw@di8b6mmhh"
# ─────────────────────────────────────────────────────────────────────────────


try:
    import cloudinary, cloudinary.uploader
    from sqlalchemy import create_engine, text
except ImportError:
    print("❌ Run: pip install cloudinary sqlalchemy psycopg2-binary")
    sys.exit(1)

# Configure Cloudinary
_p = urlparse(CLOUDINARY_URL)
cloudinary.config(cloud_name=_p.hostname, api_key=_p.username, api_secret=_p.password)
print(f"✅ Cloudinary connected: {_p.hostname}")

# Connect to PostgreSQL
engine = create_engine(PG_URL)
with engine.connect() as c:
    c.execute(text("SELECT 1"))
print("✅ PostgreSQL connected")

# Upload all images and collect mapping: old_filename → new_cloudinary_url
mapping = {}  # e.g. "board/abc123.jpg" → "https://res.cloudinary.com/..."

for folder in ["board", "events", "gallery", "misc", "slides", "toppers"]:
    folder_path = os.path.join(UPLOADS_FOLDER, folder)
    if not os.path.exists(folder_path):
        continue
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        if not os.path.isfile(filepath):
            continue
        rel_path = f"{folder}/{filename}"
        public_id = f"school/{folder}/{os.path.splitext(filename)[0]}"
        try:
            result = cloudinary.uploader.upload(
                filepath,
                public_id=public_id,
                overwrite=True,
                resource_type="image"
            )
            mapping[filename] = result["secure_url"]
            mapping[rel_path] = result["secure_url"]
            print(f"  ✅ {rel_path} → {result['secure_url']}")
        except Exception as e:
            print(f"  ❌ {rel_path}: {e}")

print(f"\nUploaded {len(mapping)//2} images. Updating database...")

# Update database columns that store image filenames
UPDATES = [
    ("board_members", "photo"),
    ("events",        "banner_image"),
    ("gallery_images","filename"),
    ("gallery_albums","cover_image"),
    ("slides",        "image"),
    ("testimonials",  "avatar"),
    ("homepage_content", "image"),
]

with engine.connect() as conn:
    for table, col in UPDATES:
        try:
            rows = conn.execute(text(f"SELECT id, {col} FROM {table} WHERE {col} IS NOT NULL")).fetchall()
            for row in rows:
                old_val = row[1]
                if not old_val or old_val.startswith("http"):
                    continue
                # Try matching just filename or folder/filename
                new_url = mapping.get(old_val) or mapping.get(os.path.basename(old_val))
                if new_url:
                    conn.execute(text(f"UPDATE {table} SET {col} = :url WHERE id = :id"),
                                 {"url": new_url, "id": row[0]})
                    print(f"  ✅ {table}.{col} id={row[0]}: {old_val} → {new_url}")
        except Exception as e:
            print(f"  ⚠ {table}.{col}: {e}")
    conn.commit()

print("\n🎉 All images uploaded to Cloudinary and database updated!")
print("Now commit and push app.py, then redeploy on Render.")
