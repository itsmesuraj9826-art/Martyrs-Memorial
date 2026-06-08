"""
seed_samples.py — Generates colorful sample images and populates the DB
Run ONCE after app.py is working:
    python3 seed_samples.py
"""
import os, sys, random
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

# ── Bootstrap Flask app context ──
sys.path.insert(0, os.path.dirname(__file__))
from app import app, db
from app.models import *  # noqa — handled below
# Import models directly from app.py (single-file setup)
from app import (GalleryAlbum, GalleryImage, BlogPost, Event,
                 HomepageContent, Testimonial, Notice)

UPLOAD = os.path.join(os.path.dirname(__file__), 'static', 'uploads')

# ── Color palettes for sample images ──
PALETTES = [
    [(27,45,69),(201,168,76)],    # navy + gold
    [(13,27,42),(232,208,138)],   # ink + light gold
    [(36,56,82),(249,250,251)],   # mid navy + white
    [(15,56,100),(255,200,80)],   # deep blue + yellow
    [(60,90,120),(255,255,255)],  # slate + white
    [(100,60,30),(255,220,100)],  # brown + gold
]

def make_image(path, w, h, title, subtitle='', palette_idx=0):
    """Create a beautiful gradient placeholder image with text."""
    c1, c2 = PALETTES[palette_idx % len(PALETTES)]
    img = Image.new('RGB', (w, h), c1)
    draw = ImageDraw.Draw(img)

    # Gradient overlay (simulate)
    for y in range(h):
        ratio = y / h
        r = int(c1[0] * (1 - ratio * 0.4) + c2[0] * ratio * 0.15)
        g = int(c1[1] * (1 - ratio * 0.4) + c2[1] * ratio * 0.15)
        b = int(c1[2] * (1 - ratio * 0.4) + c2[2] * ratio * 0.15)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    # Decorative diagonal lines
    for i in range(-h, w + h, 60):
        draw.line([(i, 0), (i + h, h)], fill=(*c2, 15), width=1)

    # Gold accent bar at bottom
    draw.rectangle([(0, h-6), (w, h)], fill=c2)

    # Center circle decoration
    cx, cy = w // 2, h // 2
    draw.ellipse([(cx-60, cy-60), (cx+60, cy+60)],
                 outline=(*c2, 120), width=2)
    draw.ellipse([(cx-40, cy-40), (cx+40, cy+40)],
                 outline=(*c2, 80), width=1)

    # Title text (large)
    try:
        font_large = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 28)
        font_small = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 16)
    except:
        font_large = ImageFont.load_default()
        font_small = font_large

    # Draw text shadow then text
    for dx, dy in [(2,2),(1,1)]:
        draw.text((w//2 + dx, cy - 15 + dy), title,
                  fill=(0,0,0,80), font=font_large, anchor='mm')
    draw.text((w//2, cy - 15), title, fill=c2, font=font_large, anchor='mm')

    if subtitle:
        draw.text((w//2, cy + 20), subtitle, fill=(255,255,255,180),
                  font=font_small, anchor='mm')

    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, quality=90)
    return os.path.basename(path)


with app.app_context():
    print("🎨 Generating sample images and seeding data...")

    # ── Gallery Albums ──────────────────────────────────────────────────────
    album_data = [
        ('Annual Sports Day 2024',   'Highlights from our annual athletic competition', 6),
        ('Science Fair 2024',        'Students showcase innovative projects',           5),
        ('Cultural Festival',        'Celebrating diversity through art and music',     6),
        ('Graduation Ceremony',      'Class of 2024 celebrates their achievement',      5),
        ('Campus Life',              'Day-to-day moments from around campus',           6),
        ('Art Exhibition',           'Student artwork on display',                      4),
    ]

    for i, (name, desc, count) in enumerate(album_data):
        if GalleryAlbum.query.filter_by(name=name).first():
            print(f"  Album '{name}' exists — skipped")
            continue
        album = GalleryAlbum(name=name, description=desc, is_published=True)
        db.session.add(album)
        db.session.flush()

        cover = None
        for j in range(count):
            fname = f'album{album.id}_img{j}.jpg'
            fpath = os.path.join(UPLOAD, 'gallery', fname)
            make_image(fpath, 800, 600, name, f'Photo {j+1}', palette_idx=i+j)
            img_obj = GalleryImage(album_id=album.id, filename=fname,
                                   caption=f'{name} — Photo {j+1}', sort_order=j)
            db.session.add(img_obj)
            if j == 0:
                cover = fname

        album.cover_image = cover
        print(f"  ✓ Album '{name}' with {count} images")

    db.session.commit()

    # ── Blog Posts ──────────────────────────────────────────────────────────
    posts_data = [
        ('Students Win National Science Olympiad', 'achievement',
         'Our talented students brought home gold at the National Science Olympiad, competing against over 500 schools nationwide. This remarkable achievement reflects months of dedicated preparation and the exceptional guidance of our science faculty.',
         True),
        ('New Computer Lab Inauguration', 'announcement',
         'We are thrilled to announce the inauguration of our state-of-the-art computer laboratory, equipped with the latest hardware and software to prepare students for the digital future.',
         True),
        ('Annual Sports Day 2024 Recap', 'sports',
         'This year\'s Annual Sports Day was a spectacular showcase of athleticism, teamwork and school spirit. Students from all grades competed in track, field, and team events.',
         True),
        ('Cultural Festival 2024 Highlights', 'cultural',
         'The Annual Cultural Festival brought together students, parents and faculty for a vibrant celebration of art, music, dance and food from around the world.',
         False),
        ('Parent-Teacher Meeting Summary', 'news',
         'Thank you to all parents who attended this term\'s Parent-Teacher Meeting. Your engagement is vital to student success and we appreciate your continued partnership.',
         False),
    ]

    for i, (title, cat, body, featured) in enumerate(posts_data):
        slug = title.lower().replace(' ', '-').replace("'", '')
        if BlogPost.query.filter_by(slug=slug).first():
            print(f"  Post '{title}' exists — skipped")
            continue
        fname = f'blog_{i}.jpg'
        fpath = os.path.join(UPLOAD, 'blog', fname)
        make_image(fpath, 1200, 630, title[:30], cat.title(), palette_idx=i+2)
        post = BlogPost(title=title, slug=slug, content=body,
                        excerpt=body[:150] + '...', category=cat,
                        featured_image=fname, is_published=True,
                        is_featured=featured)
        db.session.add(post)
        print(f"  ✓ Blog post '{title}'")

    db.session.commit()

    # ── Events ──────────────────────────────────────────────────────────────
    events_data = [
        ('Annual Sports Day 2025',       30,  'School Sports Ground',   'Join us for an exciting day of athletics, field events, and friendly competition.'),
        ('Parent-Teacher Meeting',        14,  'Main Hall',              'An opportunity to meet your child\'s teachers and discuss academic progress.'),
        ('Science Exhibition',            45,  'Science Block',          'Students present their innovative science projects to peers, parents and judges.'),
        ('Cultural Evening 2025',         60,  'School Auditorium',      'A spectacular evening of music, dance, drama and art by our talented students.'),
        ('Admission Open Day',             7,  'Reception Hall',         'Prospective families are welcome to tour our campus and meet our faculty.'),
    ]

    for title, days, loc, desc in events_data:
        if Event.query.filter_by(title=title).first():
            continue
        fname = f'event_{title[:10].lower().replace(" ","_")}.jpg'
        fpath = os.path.join(UPLOAD, 'events', fname)
        make_image(fpath, 1200, 600, title[:25], loc, palette_idx=days % 6)
        ev = Event(title=title, description=desc, location=loc,
                   event_date=datetime.utcnow() + timedelta(days=days),
                   banner_image=fname, is_published=True)
        db.session.add(ev)
        print(f"  ✓ Event '{title}'")

    db.session.commit()

    # ── Testimonials ────────────────────────────────────────────────────────
    testimonials_data = [
        ('Mrs. Priya Sharma',    'Parent of Class 10 Student',
         'Greenwood Academy has been a transformative experience for our daughter. The dedicated teachers, excellent facilities and emphasis on character building make it truly exceptional.', 5),
        ('Rahul Verma',          'Alumni, Class of 2020',
         'The values and work ethic I developed at Greenwood have been the foundation of my university success. I am forever grateful to my teachers who believed in me.', 5),
        ('Dr. Anita Mehta',      'Parent of Class 7 Student',
         'The holistic approach to education here is remarkable. My son has grown not just academically but as a confident, compassionate young person.', 5),
        ('Sunita & Raj Kapoor',  'Parents of Two Students',
         'Both our children attend Greenwood and we couldn\'t be happier. The school community is warm, inclusive and truly committed to every child\'s success.', 5),
        ('Arjun Nair',           'Alumni, Class of 2022',
         'Greenwood shaped who I am today. The teachers went above and beyond, the friendships I made here are for life, and the campus is simply beautiful.', 5),
    ]

    existing = Testimonial.query.count()
    if existing < 3:
        for i, (name, role, content_text, rating) in enumerate(testimonials_data):
            if Testimonial.query.filter_by(name=name).first():
                continue
            # Make avatar
            fname = f'avatar_{i}.jpg'
            fpath = os.path.join(UPLOAD, 'misc', fname)
            img = Image.new('RGB', (200, 200), PALETTES[i % len(PALETTES)][0])
            draw = ImageDraw.Draw(img)
            draw.ellipse([(10,10),(190,190)], fill=PALETTES[i % len(PALETTES)][1])
            try:
                font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 80)
            except:
                font = ImageFont.load_default()
            draw.text((100, 100), name[0], fill=PALETTES[i % len(PALETTES)][0],
                      font=font, anchor='mm')
            img.save(fpath)
            t = Testimonial(name=name, role=role, content=content_text,
                            rating=rating, avatar=fname, is_published=True, sort_order=i)
            db.session.add(t)
            print(f"  ✓ Testimonial from '{name}'")

        db.session.commit()

    # ── Hero image ──────────────────────────────────────────────────────────
    hero = HomepageContent.query.filter_by(section='hero').first()
    if hero and not hero.image:
        fname = 'hero_bg.jpg'
        fpath = os.path.join(UPLOAD, 'misc', fname)
        make_image(fpath, 1920, 900, 'Welcome to Excellence', 'Greenwood Academy', palette_idx=0)
        hero.image = fname
        db.session.commit()
        print("  ✓ Hero background image created")

    print("\n🎉 Sample data ready! Refresh your website to see everything.")
