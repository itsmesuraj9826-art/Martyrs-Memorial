"""
app.py — Single-file Flask School Website (with Cloudinary Integration)
==========================================================================
Requirements:
    pip install Flask Flask-SQLAlchemy Flask-Login Flask-WTF Flask-Migrate \
                PyMySQL cryptography Werkzeug WTForms Pillow python-dotenv \
                email-validator bleach cloudinary flask-mail

MySQL Setup (run once in MySQL Workbench or CLI):
    CREATE DATABASE school_website CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

Then run this file:
    python app.py

On first run it will create all tables and seed the default admin:
    URL  : http://localhost:5000
    Admin: http://localhost:5000/auth/login
    User : msuraj24  |  Password: suraj@123

Change the password immediately after first login!
"""

# ─────────────────────────────────────────────
# 0. IMPORTS
# ─────────────────────────────────────────────
import os
import re

# Load .env file FIRST so all os.environ.get() calls below pick it up
from dotenv import load_dotenv
load_dotenv()
import uuid
import unicodedata
from datetime import datetime, timedelta, timezone
from functools import wraps
from urllib.parse import quote_plus

import secrets
import bleach
import cloudinary
import cloudinary.uploader
import cloudinary.api
from flask_mail import Mail, Message as MailMessage
from flask import (Flask, Blueprint, render_template, request, redirect,
                   url_for, flash, abort, send_from_directory, current_app,
                   get_flashed_messages)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         login_required, current_user)
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from markupsafe import Markup
from werkzeug.utils import secure_filename
from wtforms import (StringField, PasswordField, TextAreaField, BooleanField,
                     SelectField, DateField, DateTimeLocalField, IntegerField,
                     SubmitField)
from wtforms.validators import (DataRequired, Length, Email, Optional,
                                EqualTo, NumberRange)
from PIL import Image


def utc_now():
    """Return current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)


def utc_now_naive():
    """Return current UTC datetime WITHOUT timezone (for comparing with DB naive columns)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ─────────────────────────────────────────────
# 1. CONFIGURATION
# ─────────────────────────────────────────────
basedir = os.path.abspath(os.path.dirname(__file__))

# ── Cloudinary configuration ──────────────────────────────────────────────────
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY    = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

CLOUDINARY_ENABLED = all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET])

if CLOUDINARY_ENABLED:
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
    )
    print("✓ Cloudinary configured successfully")
else:
    print("⚠ Cloudinary not configured — using local file storage")
    print("  Set CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET in .env")

# ── Database ──────────────────────────────────────────────────────────────────
DB_USER     = os.environ.get('DB_USER',     'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'suraj@123')
DB_HOST     = os.environ.get('DB_HOST',     'localhost')
DB_NAME     = os.environ.get('DB_NAME',     'school_website')

_raw_url = os.environ.get('DATABASE_URL')
if _raw_url:
    if _raw_url.startswith('postgres://'):
        _raw_url = _raw_url.replace('postgres://', 'postgresql+psycopg://', 1)
    elif _raw_url.startswith('postgresql://') and 'psycopg' not in _raw_url:
        _raw_url = _raw_url.replace('postgresql://', 'postgresql+psycopg://', 1)
    DATABASE_URL = _raw_url
else:
    DATABASE_URL = 'mysql+pymysql://{}:{}@{}/{}'.format(
        quote_plus(DB_USER), quote_plus(DB_PASSWORD), DB_HOST, DB_NAME
    )

UPLOAD_FOLDER      = os.path.join(basedir, 'static', 'uploads')
ALLOWED_IMAGE_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_DOC_EXTS   = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip'}

SCHOOL_NAME    = os.environ.get('SCHOOL_NAME',    "Martyrs' Memorial +2")
SCHOOL_TAGLINE = os.environ.get('SCHOOL_TAGLINE', 'Biratnagar-10, College Road')

# ── Email ─────────────────────────────────────────────────────────────────────
MAIL_SERVER_HOST  = os.environ.get('MAIL_SERVER',   'smtp.gmail.com')
MAIL_SERVER_PORT  = int(os.environ.get('MAIL_PORT', '587'))
MAIL_USE_TLS_VAL  = True
MAIL_USERNAME_VAL = os.environ.get('MAIL_USERNAME', 'surajmehta9826@gmail.com')
MAIL_PASSWORD_VAL = os.environ.get('MAIL_PASSWORD', 'akzynlwaajmdvxkg')
MAIL_RECEIVER     = os.environ.get('MAIL_RECEIVER', 'surajmehta9826@gmail.com')


# ─────────────────────────────────────────────
# 2. FLASK APP + EXTENSIONS
# ─────────────────────────────────────────────
app = Flask(__name__)
app.config.update(
    SECRET_KEY                     = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production'),
    SQLALCHEMY_DATABASE_URI        = DATABASE_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS = False,
    WTF_CSRF_ENABLED               = True,
    WTF_CSRF_TIME_LIMIT            = 3600,
    UPLOAD_FOLDER                  = UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH             = 16 * 1024 * 1024,
    ALLOWED_IMAGE_EXTENSIONS       = ALLOWED_IMAGE_EXTS,
    ALLOWED_DOC_EXTENSIONS         = ALLOWED_DOC_EXTS,
    PERMANENT_SESSION_LIFETIME     = timedelta(hours=2),
    SESSION_COOKIE_HTTPONLY        = True,
    SESSION_COOKIE_SAMESITE        = 'Lax',
    POSTS_PER_PAGE                 = 10,
    SCHOOL_NAME                    = SCHOOL_NAME,
    SCHOOL_TAGLINE                 = SCHOOL_TAGLINE,
    DEBUG                          = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true',
    MAIL_SERVER                    = MAIL_SERVER_HOST,
    MAIL_PORT                      = MAIL_SERVER_PORT,
    MAIL_USE_TLS                   = MAIL_USE_TLS_VAL,
    MAIL_USERNAME                  = MAIL_USERNAME_VAL,
    MAIL_PASSWORD                  = MAIL_PASSWORD_VAL,
    MAIL_DEFAULT_SENDER            = MAIL_USERNAME_VAL,
    CLOUDINARY_ENABLED             = CLOUDINARY_ENABLED,
)

db            = SQLAlchemy(app)
csrf          = CSRFProtect(app)
mail          = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view             = 'auth.login'
login_manager.login_message          = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# Ensure local upload sub-directories exist
for _sub in ('notices', 'events', 'gallery', 'downloads', 'blog', 'misc', 'board', 'toppers'):
    os.makedirs(os.path.join(UPLOAD_FOLDER, _sub), exist_ok=True)


# ─────────────────────────────────────────────
# 3. UTILITY FUNCTIONS
# ─────────────────────────────────────────────

def save_file(file_obj, subfolder, resize=None):
    """Save to Cloudinary if configured, otherwise save locally. Returns URL/path."""
    if not file_obj or not file_obj.filename:
        return None

    if CLOUDINARY_ENABLED:
        try:
            ext      = file_obj.filename.rsplit('.', 1)[-1].lower() if '.' in file_obj.filename else ''
            is_image = ext in ALLOWED_IMAGE_EXTS

            upload_options = {
                'folder':          f'school_website/{subfolder}',
                'use_filename':    True,
                'unique_filename': True,
            }
            if is_image and resize:
                upload_options['transformation'] = [
                    {'width': resize[0], 'height': resize[1], 'crop': 'limit'}
                ]
            result = cloudinary.uploader.upload(file_obj, **upload_options)
            return result.get('secure_url')
        except Exception as e:
            app.logger.error(f"Cloudinary upload error: {e}")
            return _save_file_local(file_obj, subfolder, resize)
    else:
        return _save_file_local(file_obj, subfolder, resize)


def _save_file_local(file_obj, subfolder, resize=None):
    """Local file storage fallback."""
    original  = secure_filename(file_obj.filename)
    ext       = original.rsplit('.', 1)[-1].lower() if '.' in original else 'bin'
    unique    = f"{uuid.uuid4().hex}.{ext}"
    dest_dir  = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, unique)
    file_obj.save(dest_path)

    if resize and ext in app.config['ALLOWED_IMAGE_EXTENSIONS']:
        try:
            img = Image.open(dest_path)
            img.thumbnail(resize, Image.LANCZOS)
            img.save(dest_path, optimize=True, quality=85)
        except Exception:
            pass

    return f'/static/uploads/{subfolder}/{unique}'


def delete_file(file_path, subfolder):
    """Delete from Cloudinary (if URL) or local storage."""
    if not file_path:
        return

    if CLOUDINARY_ENABLED and file_path.startswith('http'):
        try:
            parts = file_path.split('/')
            for i, part in enumerate(parts):
                if part in ['upload', 'image', 'video', 'raw'] and i + 1 < len(parts):
                    start = i + 1
                    if parts[start].startswith('v') and parts[start][1:].isdigit():
                        start += 1
                    public_id = '/'.join(parts[start:]).split('.')[0]
                    cloudinary.uploader.destroy(public_id)
                    return
        except Exception as e:
            app.logger.error(f"Cloudinary delete error: {e}")

    if file_path and not file_path.startswith('http'):
        filename = os.path.basename(file_path)
        path     = os.path.join(app.config['UPLOAD_FOLDER'], subfolder, filename)
        if os.path.exists(path):
            os.remove(path)


def allowed_image(filename):
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    return ext in app.config['ALLOWED_IMAGE_EXTENSIONS']


def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')


_ALLOWED_TAGS = [
    'a', 'abbr', 'b', 'blockquote', 'br', 'code', 'em',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'li',
    'ol', 'p', 'pre', 's', 'strong', 'table', 'tbody', 'td', 'th',
    'thead', 'tr', 'u', 'ul',
]
_ALLOWED_ATTRS = {
    '*':   ['class', 'style'],
    'a':   ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'td':  ['colspan', 'rowspan'],
    'th':  ['colspan', 'rowspan'],
}


def sanitize_html(content):
    if not content:
        return ''
    return bleach.clean(content, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS, strip=True)


# ─────────────────────────────────────────────
# 4. MODELS
# ─────────────────────────────────────────────

class Admin(UserMixin, db.Model):
    __tablename__      = 'admins'
    id                 = db.Column(db.Integer,     primary_key=True)
    username           = db.Column(db.String(80),  unique=True, nullable=False, index=True)
    email              = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash      = db.Column(db.String(255), nullable=False)
    full_name          = db.Column(db.String(150), nullable=False)
    is_active          = db.Column(db.Boolean,     default=True, nullable=False)
    created_at         = db.Column(db.DateTime,    default=utc_now)
    last_login         = db.Column(db.DateTime,    nullable=True)
    reset_token        = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime,    nullable=True)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))


class Notice(db.Model):
    __tablename__ = 'notices'
    id            = db.Column(db.Integer,     primary_key=True)
    title         = db.Column(db.String(255), nullable=False)
    content       = db.Column(db.Text,        nullable=False)
    category      = db.Column(db.String(50),  default='general')
    is_pinned     = db.Column(db.Boolean,     default=False)
    is_published  = db.Column(db.Boolean,     default=True)
    attachment    = db.Column(db.String(500), nullable=True)
    expiry_date   = db.Column(db.Date,        nullable=True)
    created_at    = db.Column(db.DateTime,    default=utc_now, index=True)
    updated_at    = db.Column(db.DateTime,    default=utc_now, onupdate=utc_now)

    def is_expired(self):
        if self.expiry_date is None:
            return False
        return self.expiry_date < utc_now().date()


class Event(db.Model):
    __tablename__ = 'events'
    id            = db.Column(db.Integer,     primary_key=True)
    title         = db.Column(db.String(255), nullable=False)
    description   = db.Column(db.Text,        nullable=False)
    location      = db.Column(db.String(255), nullable=True)
    event_date    = db.Column(db.DateTime,    nullable=False, index=True)
    end_date      = db.Column(db.DateTime,    nullable=True)
    banner_image  = db.Column(db.String(500), nullable=True)
    is_published  = db.Column(db.Boolean,     default=True)
    created_at    = db.Column(db.DateTime,    default=utc_now)
    updated_at    = db.Column(db.DateTime,    default=utc_now, onupdate=utc_now)

    def is_upcoming(self):
        # event_date is stored as naive datetime; compare with naive UTC now
        return self.event_date >= datetime.now(timezone.utc).replace(tzinfo=None)


class GalleryAlbum(db.Model):
    __tablename__ = 'gallery_albums'
    id            = db.Column(db.Integer,     primary_key=True)
    name          = db.Column(db.String(150), nullable=False)
    description   = db.Column(db.Text,        nullable=True)
    cover_image   = db.Column(db.String(500), nullable=True)
    is_published  = db.Column(db.Boolean,     default=True)
    created_at    = db.Column(db.DateTime,    default=utc_now)
    images        = db.relationship('GalleryImage', backref='album', lazy='dynamic',
                                    cascade='all, delete-orphan')

    def image_count(self):
        return self.images.count()


class GalleryImage(db.Model):
    __tablename__ = 'gallery_images'
    id            = db.Column(db.Integer,     primary_key=True)
    album_id      = db.Column(db.Integer,     db.ForeignKey('gallery_albums.id', ondelete='CASCADE'),
                              nullable=False,  index=True)
    filename      = db.Column(db.String(500), nullable=False)
    caption       = db.Column(db.String(255), nullable=True)
    sort_order    = db.Column(db.Integer,     default=0)
    created_at    = db.Column(db.DateTime,    default=utc_now)


class BlogPost(db.Model):
    __tablename__  = 'blog_posts'
    id             = db.Column(db.Integer,     primary_key=True)
    title          = db.Column(db.String(255), nullable=False)
    slug           = db.Column(db.String(255), unique=True, nullable=False, index=True)
    content        = db.Column(db.Text,        nullable=False)
    excerpt        = db.Column(db.Text,        nullable=True)
    featured_image = db.Column(db.String(500), nullable=True)
    category       = db.Column(db.String(80),  default='news')
    is_published   = db.Column(db.Boolean,     default=True)
    is_featured    = db.Column(db.Boolean,     default=False)
    views          = db.Column(db.Integer,     default=0)
    created_at     = db.Column(db.DateTime,    default=utc_now, index=True)
    updated_at     = db.Column(db.DateTime,    default=utc_now, onupdate=utc_now)


class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'
    id            = db.Column(db.Integer,     primary_key=True)
    name          = db.Column(db.String(150), nullable=False)
    email         = db.Column(db.String(150), nullable=False)
    phone         = db.Column(db.String(20),  nullable=True)
    subject       = db.Column(db.String(255), nullable=False)
    message       = db.Column(db.Text,        nullable=False)
    is_read       = db.Column(db.Boolean,     default=False)
    created_at    = db.Column(db.DateTime,    default=utc_now, index=True)


class Download(db.Model):
    __tablename__  = 'downloads'
    id             = db.Column(db.Integer,     primary_key=True)
    title          = db.Column(db.String(255), nullable=False)
    description    = db.Column(db.Text,        nullable=True)
    filename       = db.Column(db.String(500), nullable=False)
    original_name  = db.Column(db.String(255), nullable=False)
    category       = db.Column(db.String(80),  default='general')
    file_size      = db.Column(db.Integer,     nullable=True)
    download_count = db.Column(db.Integer,     default=0)
    is_published   = db.Column(db.Boolean,     default=True)
    created_at     = db.Column(db.DateTime,    default=utc_now, index=True)

    def formatted_size(self):
        if not self.file_size:
            return 'Unknown'
        if self.file_size < 1024:
            return f'{self.file_size} B'
        elif self.file_size < 1024 * 1024:
            return f'{self.file_size / 1024:.1f} KB'
        return f'{self.file_size / (1024 * 1024):.1f} MB'


class HomepageContent(db.Model):
    __tablename__ = 'homepage_content'
    id            = db.Column(db.Integer,     primary_key=True)
    section       = db.Column(db.String(80),  unique=True, nullable=False)
    title         = db.Column(db.String(255), nullable=True)
    subtitle      = db.Column(db.String(255), nullable=True)
    content       = db.Column(db.Text,        nullable=True)
    image         = db.Column(db.String(500), nullable=True)
    extra_data    = db.Column(db.JSON,        nullable=True)
    updated_at    = db.Column(db.DateTime,    default=utc_now, onupdate=utc_now)


class Slide(db.Model):
    __tablename__ = 'slides'
    id            = db.Column(db.Integer,     primary_key=True)
    title         = db.Column(db.String(255), nullable=True)
    subtitle      = db.Column(db.String(255), nullable=True)
    image         = db.Column(db.String(500), nullable=False)
    btn_text      = db.Column(db.String(80),  nullable=True, default='Learn More')
    btn_url       = db.Column(db.String(255), nullable=True)
    sort_order    = db.Column(db.Integer,     default=0)
    is_active     = db.Column(db.Boolean,     default=True)
    created_at    = db.Column(db.DateTime,    default=utc_now)


class BoardMember(db.Model):
    __tablename__ = 'board_members'
    id            = db.Column(db.Integer,     primary_key=True)
    name          = db.Column(db.String(150), nullable=False)
    position      = db.Column(db.String(150), nullable=False)
    category      = db.Column(db.String(80),  default='board')
    bio           = db.Column(db.Text,        nullable=True)
    photo         = db.Column(db.String(500), nullable=True)
    email         = db.Column(db.String(120), nullable=True)
    phone         = db.Column(db.String(30),  nullable=True)
    is_published  = db.Column(db.Boolean,     default=True)
    sort_order    = db.Column(db.Integer,     default=0)
    created_at    = db.Column(db.DateTime,    default=utc_now)
    updated_at    = db.Column(db.DateTime,    default=utc_now, onupdate=utc_now)


class Testimonial(db.Model):
    __tablename__ = 'testimonials'
    id            = db.Column(db.Integer,     primary_key=True)
    name          = db.Column(db.String(150), nullable=False)
    role          = db.Column(db.String(150), nullable=True)
    content       = db.Column(db.Text,        nullable=False)
    avatar        = db.Column(db.String(500), nullable=True)
    rating        = db.Column(db.Integer,     default=5)
    is_published  = db.Column(db.Boolean,     default=True)
    sort_order    = db.Column(db.Integer,     default=0)
    created_at    = db.Column(db.DateTime,    default=utc_now)


class Topper(db.Model):
    __tablename__ = 'toppers'
    id            = db.Column(db.Integer,        primary_key=True)
    name          = db.Column(db.String(150),    nullable=False)
    stream        = db.Column(db.String(50),     nullable=False)
    percentage    = db.Column(db.Numeric(5, 2),  nullable=True)
    year          = db.Column(db.String(10),     nullable=False, default='2024')
    photo         = db.Column(db.String(500),    nullable=True)
    rank          = db.Column(db.Integer,        default=1)
    is_published  = db.Column(db.Boolean,        default=True)
    sort_order    = db.Column(db.Integer,        default=0)
    created_at    = db.Column(db.DateTime,       default=utc_now)


class FooterTheme(db.Model):
    """Controls the footer event theme — set by admin."""
    __tablename__ = 'footer_theme'
    id         = db.Column(db.Integer,     primary_key=True)
    theme      = db.Column(db.String(30),  default='default')
    label      = db.Column(db.String(100), nullable=True)
    subtext    = db.Column(db.String(200), nullable=True)
    cta_text   = db.Column(db.String(60),  nullable=True)
    cta_url    = db.Column(db.String(255), nullable=True)
    image      = db.Column(db.String(500), nullable=True)   # event photo / poster
    is_active  = db.Column(db.Boolean,     default=False)
    updated_at = db.Column(db.DateTime,    default=utc_now, onupdate=utc_now)


# ─────────────────────────────────────────────
# 5. FORMS
# ─────────────────────────────────────────────

class LoginForm(FlaskForm):
    username    = StringField('Username',  validators=[DataRequired(), Length(1, 80)])
    password    = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit      = SubmitField('Log In')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password     = PasswordField('New Password',
                                     validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password',
                                     validators=[DataRequired(),
                                                 EqualTo('new_password', message='Passwords must match.')])
    submit = SubmitField('Update Password')


class ContactForm(FlaskForm):
    name    = StringField('Your Name',         validators=[DataRequired(), Length(1, 150)])
    email   = StringField('Email Address',     validators=[DataRequired(), Email()])
    phone   = StringField('Phone Number',      validators=[Optional(), Length(0, 20)])
    stream  = SelectField('Programme / Stream', validators=[Optional()], choices=[
        ('', '— Select Programme (optional) —'),
        ('science_bio',  'Science (With Biology)'),
        ('science_math', 'Science (Without Biology / Math)'),
        ('management',   'Management'),
        ('law',          'Law'),
        ('arts',         'Arts / Humanities'),
        ('other',        'Other / General Enquiry'),
    ])
    subject = StringField('Subject',   validators=[DataRequired(), Length(1, 255)])
    message = TextAreaField('Message', validators=[DataRequired(), Length(min=10)])
    submit  = SubmitField('Send Message')


class NoticeForm(FlaskForm):
    title        = StringField('Title',   validators=[DataRequired(), Length(1, 255)])
    content      = TextAreaField('Content', validators=[DataRequired()])
    category     = SelectField('Category', choices=[
        ('general', 'General'), ('academic', 'Academic'), ('exam', 'Examination'),
        ('event', 'Event'), ('urgent', 'Urgent')])
    is_pinned    = BooleanField('Pin this notice')
    is_published = BooleanField('Publish', default=True)
    expiry_date  = DateField('Expiry Date', validators=[Optional()], format='%Y-%m-%d')
    attachment   = FileField('Attachment', validators=[
        Optional(),
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'],
                    'Allowed: PDF, Word, Excel, Images')])
    submit = SubmitField('Save Notice')


class EventForm(FlaskForm):
    title        = StringField('Title',       validators=[DataRequired(), Length(1, 255)])
    description  = TextAreaField('Description', validators=[DataRequired()])
    location     = StringField('Location',    validators=[Optional(), Length(0, 255)])
    event_date   = DateTimeLocalField('Event Date & Time', format='%Y-%m-%dT%H:%M',
                                      validators=[DataRequired()])
    end_date     = DateTimeLocalField('End Date & Time (optional)', format='%Y-%m-%dT%H:%M',
                                      validators=[Optional()])
    banner_image = FileField('Banner Image', validators=[
        Optional(), FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'webp'], 'Images only.')])
    is_published = BooleanField('Publish', default=True)
    submit       = SubmitField('Save Event')


class AlbumForm(FlaskForm):
    name         = StringField('Album Name', validators=[DataRequired(), Length(1, 150)])
    description  = TextAreaField('Description', validators=[Optional()])
    is_published = BooleanField('Publish', default=True)
    submit       = SubmitField('Save Album')


class ImageUploadForm(FlaskForm):
    images = MultipleFileField('Images', validators=[DataRequired()])
    submit = SubmitField('Upload Images')


class BlogPostForm(FlaskForm):
    title          = StringField('Title',   validators=[DataRequired(), Length(1, 255)])
    content        = TextAreaField('Content', validators=[DataRequired()])
    excerpt        = TextAreaField('Excerpt (Short Summary)', validators=[Optional(), Length(0, 500)])
    category       = SelectField('Category', choices=[
        ('news', 'School News'), ('announcement', 'Announcement'),
        ('achievement', 'Achievement'), ('sports', 'Sports'), ('cultural', 'Cultural')])
    featured_image = FileField('Featured Image', validators=[
        Optional(), FileAllowed(['png', 'jpg', 'jpeg', 'gif', 'webp'], 'Images only.')])
    is_published   = BooleanField('Publish', default=True)
    is_featured    = BooleanField('Feature on Homepage')
    submit         = SubmitField('Save Post')


class DownloadForm(FlaskForm):
    title        = StringField('Title',       validators=[DataRequired(), Length(1, 255)])
    description  = TextAreaField('Description', validators=[Optional()])
    category     = SelectField('Category', choices=[
        ('admission', 'Admission Forms'), ('syllabus', 'Syllabus'),
        ('calendar', 'Academic Calendar'), ('brochure', 'Brochure'),
        ('notice', 'Notice'), ('general', 'General')])
    file         = FileField('File', validators=[
        DataRequired(),
        FileAllowed(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip'],
                    'Allowed: PDF, Word, Excel, PowerPoint, ZIP')])
    is_published = BooleanField('Publish', default=True)
    submit       = SubmitField('Upload File')


class HomepageHeroForm(FlaskForm):
    title    = StringField('Hero Title',         validators=[DataRequired()])
    subtitle = StringField('Hero Subtitle',       validators=[Optional()])
    content  = TextAreaField('Hero Description',  validators=[Optional()])
    image    = FileField('Hero Background Image', validators=[
        Optional(), FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Images only.')])
    submit   = SubmitField('Save')


class AnnouncementPopupForm(FlaskForm):
    title    = StringField('Title',           validators=[Optional(), Length(0, 255)])
    subtitle = StringField('Subtitle/Badge',  validators=[Optional(), Length(0, 255)])
    content  = TextAreaField('Body Text',     validators=[Optional()])
    image    = FileField('Popup Image',       validators=[
        Optional(), FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Images only.')])
    submit   = SubmitField('Save Popup')


class AdminProfileForm(FlaskForm):
    full_name = StringField('Full Name',     validators=[DataRequired(), Length(1, 150)])
    email     = StringField('Email Address', validators=[DataRequired(), Email()])
    submit    = SubmitField('Update Profile')


class ForgotPasswordForm(FlaskForm):
    email  = StringField('Admin Email Address', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')


class ResetPasswordForm(FlaskForm):
    new_password     = PasswordField('New Password',
                                     validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(),
                                                 EqualTo('new_password', message='Passwords must match.')])
    submit = SubmitField('Reset Password')


class SlideForm(FlaskForm):
    title      = StringField('Slide Title',   validators=[Optional(), Length(0, 255)])
    subtitle   = StringField('Subtitle',      validators=[Optional(), Length(0, 255)])
    btn_text   = StringField('Button Label',  validators=[Optional(), Length(0, 80)], default='Learn More')
    btn_url    = StringField('Button Link',   validators=[Optional(), Length(0, 255)])
    sort_order = IntegerField('Sort Order',   validators=[Optional()], default=0)
    is_active  = BooleanField('Active',       default=True)
    image      = FileField('Slide Image (landscape, 1920×700px recommended)', validators=[
        Optional(), FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Images only.')])
    submit     = SubmitField('Save Slide')


class BoardMemberForm(FlaskForm):
    name         = StringField('Full Name',         validators=[DataRequired(), Length(1, 150)])
    position     = StringField('Position / Title',  validators=[DataRequired(), Length(1, 150)])
    category     = SelectField('Category', choices=[
        ('board',      'Board of Directors'),
        ('management', 'Management Committee'),
        ('faculty',    'Faculty / Staff'),
    ], default='board')
    bio          = TextAreaField('Short Bio',        validators=[Optional()])
    email        = StringField('Email',              validators=[Optional(), Email()])
    phone        = StringField('Phone',              validators=[Optional(), Length(0, 30)])
    sort_order   = IntegerField('Sort Order',        validators=[Optional()], default=0)
    is_published = BooleanField('Published',         default=True)
    photo        = FileField('Photo', validators=[
        Optional(), FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Images only.')])
    submit       = SubmitField('Save Member')


class TestimonialForm(FlaskForm):
    name    = StringField('Name',                       validators=[DataRequired()])
    role    = StringField('Role (e.g. Parent, Alumni)', validators=[Optional()])
    content = TextAreaField('Testimonial',              validators=[DataRequired()])
    rating  = IntegerField('Rating (1-5)', validators=[Optional(), NumberRange(1, 5)], default=5)
    avatar  = FileField('Avatar Image', validators=[
        Optional(), FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Images only.')])
    submit  = SubmitField('Save Testimonial')


class TopperForm(FlaskForm):
    name         = StringField('Student Name',   validators=[DataRequired(), Length(1, 150)])
    stream       = SelectField('Stream', choices=[
        ('science_bio',  'Science (With Biology)'),
        ('science_math', 'Science (Without Biology / Math)'),
        ('management',   'Management'),
        ('law',          'Law'),
        ('arts',         'Arts'),
    ])
    percentage   = StringField('Percentage / GPA', validators=[Optional(), Length(0, 10)])
    year         = StringField('Year (e.g. 2024)',  validators=[DataRequired(), Length(1, 10)], default='2024')
    rank         = IntegerField('Rank',             validators=[Optional(), NumberRange(1, 20)], default=1)
    sort_order   = IntegerField('Sort Order',       validators=[Optional()], default=0)
    is_published = BooleanField('Published',        default=True)
    photo        = FileField('Student Photo', validators=[
        Optional(), FileAllowed(['png', 'jpg', 'jpeg', 'webp'], 'Images only.')])
    submit       = SubmitField('Save Topper')


class FooterThemeForm(FlaskForm):
    theme    = SelectField('Event Theme', choices=[
        ('default',   '— Default (no event) —'),
        ('admission', '🎓 Admissions Open'),
        ('sports',    '🏆 Sports Day'),
        ('annual',    '🎉 Annual Day'),
        ('exam',      '📝 Exam Season'),
        ('result',    '🌟 Results Declared'),
    ])
    label    = StringField('Event Headline',     validators=[Optional(), Length(0, 100)])
    subtext  = StringField('Subtext / Details',  validators=[Optional(), Length(0, 200)])
    cta_text = StringField('Button Text',        validators=[Optional(), Length(0, 60)])
    cta_url  = StringField('Button Link (URL)',  validators=[Optional(), Length(0, 255)])
    image    = FileField('Event Photo / Poster', validators=[
                 Optional(), FileAllowed(['png','jpg','jpeg','webp'], 'Images only.')])
    is_active= BooleanField('Show event theme on website', default=True)
    submit   = SubmitField('Save Theme')


# ─────────────────────────────────────────────
# 6. CONTEXT PROCESSORS & TEMPLATE GLOBALS
# ─────────────────────────────────────────────

@app.context_processor
def inject_globals():
    ticker_notices = []
    footer_theme   = None
    try:
        ticker_notices = (Notice.query
                          .filter_by(is_published=True)
                          .order_by(Notice.is_pinned.desc(), Notice.created_at.desc())
                          .limit(8).all())
    except Exception:
        db.session.rollback()

    try:
        footer_theme = FooterTheme.query.filter_by(is_active=True).first()
    except Exception:
        db.session.rollback()   # table may not exist yet — rollback so other queries still work

    return {
        'now':                utc_now(),
        'school_name':        app.config['SCHOOL_NAME'],
        'school_tagline':     app.config['SCHOOL_TAGLINE'],
        'latest_notices':     ticker_notices,
        'cloudinary_enabled': CLOUDINARY_ENABLED,
        'footer_theme':       footer_theme,
    }


@app.template_global()
def unread_count():
    """Returns number of unread contact messages. Used in nav bell and sidebar badge."""
    try:
        return ContactMessage.query.filter_by(is_read=False).count()
    except Exception:
        db.session.rollback()
        return 0


@app.template_global()
def get_recent_messages(limit=5):
    """Returns the most recent contact messages for the notification dropdown."""
    try:
        return (ContactMessage.query
                .order_by(ContactMessage.created_at.desc())
                .limit(limit).all())
    except Exception:
        db.session.rollback()
        return []


@app.template_global()
def img_src(path_or_url, subfolder='misc'):
    """
    Resolve an image stored path or URL to a usable <img src> / CSS url().

    Handles all three storage cases:
      - Cloudinary URL  (https://res.cloudinary.com/...)  → returned as-is
      - Local abs path  (/static/uploads/misc/file.jpg)   → returned as-is
      - Bare filename   (abc123.jpg)  ← legacy            → prefixed with /static/uploads/{subfolder}/
      - None / empty                                       → navy placeholder SVG
    """
    if not path_or_url:
        # Transparent navy placeholder — prevents broken-image icons
        return (
            "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
            "width='400' height='300'%3E"
            "%3Crect width='400' height='300' fill='%231a3570'/%3E"
            "%3C/svg%3E"
        )
    # Full URL (Cloudinary) or absolute local path
    if path_or_url.startswith('http') or path_or_url.startswith('/'):
        return path_or_url
    # Bare filename — legacy local storage
    return f'/static/uploads/{subfolder}/{path_or_url}'


@app.template_global()
def csrf_token_field():
    from flask_wtf.csrf import generate_csrf
    token = generate_csrf()
    return Markup(f'<input type="hidden" name="csrf_token" value="{token}">')


# ─────────────────────────────────────────────
# 7. BLUEPRINTS
# ─────────────────────────────────────────────
public_bp = Blueprint('public', __name__)
auth_bp   = Blueprint('auth',   __name__)
admin_bp  = Blueprint('admin',  __name__)


def _require_admin(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_active:
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# 8. PUBLIC ROUTES
# ─────────────────────────────────────────────

def _get_section(section):
    return HomepageContent.query.filter_by(section=section).first()


@public_bp.route('/')
def index():
    hero      = _get_section('hero')
    about     = _get_section('about')
    principal = _get_section('principal')
    stats     = _get_section('stats')
    popup     = _get_section('popup')
    slides    = Slide.query.filter_by(is_active=True).order_by(Slide.sort_order.asc()).all()

    latest_notices  = (Notice.query.filter_by(is_published=True)
                       .order_by(Notice.is_pinned.desc(), Notice.created_at.desc())
                       .limit(5).all())
    upcoming_events = (Event.query
                       .filter(Event.is_published == True, Event.event_date >= utc_now_naive())
                       .order_by(Event.event_date.asc()).limit(4).all())
    featured_posts  = (BlogPost.query.filter_by(is_published=True, is_featured=True)
                       .order_by(BlogPost.created_at.desc()).limit(3).all())
    gallery_albums  = (GalleryAlbum.query.filter_by(is_published=True)
                       .order_by(GalleryAlbum.created_at.desc()).limit(6).all())
    testimonials    = (Testimonial.query.filter_by(is_published=True)
                       .order_by(Testimonial.sort_order.asc()).limit(6).all())

    _streams = ['science_bio', 'science_math', 'management', 'law', 'arts']
    toppers_by_stream = {}
    for s in _streams:
        toppers_by_stream[s] = (Topper.query
                                .filter_by(is_published=True, stream=s)
                                .order_by(Topper.sort_order.asc(), Topper.rank.asc())
                                .limit(20).all())

    try:
        popup_show = bool(popup and popup.extra_data and popup.extra_data.get('enabled'))
    except Exception:
        popup_show = False

    return render_template('public/index.html',
                           hero=hero, about=about, principal=principal, stats=stats,
                           popup=popup, popup_show=popup_show, slides=slides,
                           latest_notices=latest_notices, upcoming_events=upcoming_events,
                           featured_posts=featured_posts, gallery_albums=gallery_albums,
                           testimonials=testimonials,
                           toppers_by_stream=toppers_by_stream)


@public_bp.route('/about')
def about():
    board_members = (BoardMember.query
                     .filter_by(is_published=True)
                     .order_by(BoardMember.sort_order.asc(), BoardMember.name.asc())
                     .all())
    return render_template('public/about.html',
                           about=_get_section('about'),
                           principal=_get_section('principal'),
                           mission=_get_section('mission'),
                           board_members=board_members)


@public_bp.route('/academics')
def academics():
    syllabi   = Download.query.filter_by(is_published=True, category='syllabus').order_by(Download.created_at.desc()).all()
    calendars = Download.query.filter_by(is_published=True, category='calendar').order_by(Download.created_at.desc()).all()
    return render_template('public/academics.html', syllabi=syllabi, calendars=calendars)


@public_bp.route('/notices')
def notices():
    page     = request.args.get('page', 1, type=int)
    q        = request.args.get('q', '')
    category = request.args.get('category', '')
    query    = Notice.query.filter_by(is_published=True)
    if q:
        query = query.filter(Notice.title.ilike(f'%{q}%'))
    if category:
        query = query.filter_by(category=category)
    pagination = (query.order_by(Notice.is_pinned.desc(), Notice.created_at.desc())
                  .paginate(page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False))
    return render_template('public/notices.html', pagination=pagination, q=q, category=category)


@public_bp.route('/events')
def events():
    page = request.args.get('page', 1, type=int)
    tab  = request.args.get('tab', 'upcoming')
    if tab == 'past':
        query = Event.query.filter(Event.is_published == True,
                                   Event.event_date < utc_now_naive()).order_by(Event.event_date.desc())
    else:
        query = Event.query.filter(Event.is_published == True,
                                   Event.event_date >= utc_now_naive()).order_by(Event.event_date.asc())
    pagination = query.paginate(page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    return render_template('public/events.html', pagination=pagination, tab=tab)


@public_bp.route('/events/<int:event_id>')
def event_detail(event_id):
    event = Event.query.filter_by(id=event_id, is_published=True).first_or_404()
    return render_template('public/event_detail.html', event=event)


@public_bp.route('/gallery')
def gallery():
    albums = (GalleryAlbum.query.filter_by(is_published=True)
              .order_by(GalleryAlbum.created_at.desc()).all())
    return render_template('public/gallery.html', albums=albums)


@public_bp.route('/gallery/<int:album_id>')
def gallery_album(album_id):
    album  = GalleryAlbum.query.filter_by(id=album_id, is_published=True).first_or_404()
    images = album.images.order_by(GalleryImage.sort_order.asc()).all()
    return render_template('public/gallery_album.html', album=album, images=images)


@public_bp.route('/news')
def news():
    page     = request.args.get('page', 1, type=int)
    q        = request.args.get('q', '')
    category = request.args.get('category', '')
    query    = BlogPost.query.filter_by(is_published=True)
    if q:
        query = query.filter(BlogPost.title.ilike(f'%{q}%'))
    if category:
        query = query.filter_by(category=category)
    pagination = (query.order_by(BlogPost.created_at.desc())
                  .paginate(page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False))
    return render_template('public/news.html', pagination=pagination, q=q, category=category)


@public_bp.route('/news/<slug>')
def news_detail(slug):
    post        = BlogPost.query.filter_by(slug=slug, is_published=True).first_or_404()
    post.views += 1
    db.session.commit()
    return render_template('public/news_detail.html', post=post)


@public_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        msg = ContactMessage(
            name=form.name.data, email=form.email.data, phone=form.phone.data,
            subject=form.subject.data, message=form.message.data)
        db.session.add(msg)
        db.session.commit()
        _send_contact_email(form)
        _send_autoreply_email(form)
        flash('Your message has been sent. We will get back to you soon!', 'success')
        return redirect(url_for('public.contact'))
    return render_template('public/contact.html', form=form)


def _send_contact_email(form):
    receiver = app.config.get('MAIL_RECEIVER') or app.config.get('MAIL_USERNAME')
    if not receiver or not app.config.get('MAIL_USERNAME'):
        return
    try:
        stream_labels = {
            'science_bio':  'Science (With Biology)',
            'science_math': 'Science (Without Biology / Math)',
            'management':   'Management',
            'law':          'Law',
            'arts':         'Arts / Humanities',
            'other':        'Other / General Enquiry',
        }
        stream_str = stream_labels.get(form.stream.data, 'Not specified') if form.stream.data else 'Not specified'
        body = (
            f"New contact form submission from your school website.\n\n"
            f"Name      : {form.name.data}\n"
            f"Email     : {form.email.data}\n"
            f"Phone     : {form.phone.data or 'Not provided'}\n"
            f"Programme : {stream_str}\n"
            f"Subject   : {form.subject.data}\n\n"
            f"Message:\n{form.message.data}\n\n"
            f"---\nReceived at {utc_now().strftime('%Y-%m-%d %H:%M UTC')}\n"
        )
        email_msg = MailMessage(
            subject=f"[Contact Form] {form.subject.data} — from {form.name.data}",
            recipients=[receiver],
            body=body,
            reply_to=form.email.data,
        )
        mail.send(email_msg)
    except Exception as e:
        app.logger.warning(f"Admin email failed: {e}")


def _send_autoreply_email(form):
    if not app.config.get('MAIL_USERNAME'):
        return
    try:
        school = app.config['SCHOOL_NAME']
        body   = (
            f"Dear {form.name.data},\n\n"
            f"Thank you for reaching out to {school}. We have received your message "
            f"and will get back to you within 1–2 business days.\n\n"
            f"Your message details:\nSubject : {form.subject.data}\n\n"
            f"---\nThis is an automated reply. Please do not reply to this email.\n"
            f"{school} | info@martyrsmemorial.edu.np\n"
        )
        email_msg = MailMessage(
            subject=f"Thank you for contacting {school}",
            recipients=[form.email.data],
            body=body,
        )
        mail.send(email_msg)
    except Exception as e:
        app.logger.warning(f"Auto-reply email failed: {e}")


@public_bp.route('/downloads')
def downloads():
    category   = request.args.get('category', '')
    query      = Download.query.filter_by(is_published=True)
    if category:
        query  = query.filter_by(category=category)
    files      = query.order_by(Download.created_at.desc()).all()
    categories = [c[0] for c in db.session.query(Download.category)
                  .filter_by(is_published=True).distinct().all()]
    return render_template('public/downloads.html', files=files,
                           categories=categories, active_category=category)


@public_bp.route('/downloads/<int:file_id>/get')
def download_file(file_id):
    dl = Download.query.filter_by(id=file_id, is_published=True).first_or_404()
    dl.download_count += 1
    db.session.commit()
    if dl.filename and dl.filename.startswith('http'):
        return redirect(dl.filename)
    folder = os.path.join(app.config['UPLOAD_FOLDER'], 'downloads')
    return send_from_directory(folder, os.path.basename(dl.filename),
                               as_attachment=True, download_name=dl.original_name)


@public_bp.route('/notices/<int:notice_id>/attachment')
def notice_attachment(notice_id):
    notice = Notice.query.filter_by(id=notice_id, is_published=True).first_or_404()
    if not notice.attachment:
        abort(404)
    if notice.attachment.startswith('http'):
        return redirect(notice.attachment)
    folder = os.path.join(app.config['UPLOAD_FOLDER'], 'notices')
    return send_from_directory(folder, os.path.basename(notice.attachment), as_attachment=True)


@public_bp.route('/privacy-policy')
def privacy_policy():
    policy = HomepageContent.query.filter_by(section='privacy_policy').first()
    return render_template('public/privacy_policy.html', policy=policy)


# ─────────────────────────────────────────────
# 9. AUTH ROUTES
# ─────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and admin.is_active and admin.check_password(form.password.data):
            login_user(admin, remember=form.remember_me.data)
            admin.last_login = utc_now()
            db.session.commit()
            next_page = request.args.get('next')
            flash('Welcome back!', 'success')
            return redirect(next_page or url_for('admin.dashboard'))
        flash('Invalid username or password.', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Current password is incorrect.', 'danger')
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Password updated successfully.', 'success')
            return redirect(url_for('admin.dashboard'))
    return render_template('auth/change_password.html', form=form)


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(email=form.email.data).first()
        if admin:
            token                  = secrets.token_urlsafe(32)
            admin.reset_token      = token
            admin.reset_token_expiry = utc_now() + timedelta(hours=1)
            db.session.commit()
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            try:
                if app.config.get('MAIL_USERNAME'):
                    msg = MailMessage(
                        subject=f"Password Reset — {app.config['SCHOOL_NAME']} Admin",
                        recipients=[admin.email],
                        body=(
                            f"Hello {admin.full_name},\n\n"
                            f"A password reset was requested for your admin account.\n\n"
                            f"Click the link below to reset your password (valid for 1 hour):\n"
                            f"{reset_url}\n\n"
                            f"If you did not request this, ignore this email.\n\n"
                            f"— {app.config['SCHOOL_NAME']} System\n"
                        ),
                    )
                    mail.send(msg)
                    flash('Password reset link sent to your email.', 'success')
                else:
                    flash(f'Reset link (dev mode — email not configured): {reset_url}', 'info')
            except Exception as e:
                app.logger.warning(f'Reset email failed: {e}')
                flash(f'Reset link: {reset_url}', 'info')
        else:
            flash('If that email exists, a reset link has been sent.', 'success')
        return redirect(url_for('auth.forgot_password'))
    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    admin = Admin.query.filter_by(reset_token=token).first()
    if not admin or not admin.reset_token_expiry or admin.reset_token_expiry < utc_now():
        flash('This reset link is invalid or has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        admin.set_password(form.new_password.data)
        admin.reset_token        = None
        admin.reset_token_expiry = None
        db.session.commit()
        flash('Password reset successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form, token=token)


# ─────────────────────────────────────────────
# 10. ADMIN ROUTES
# ─────────────────────────────────────────────

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@_require_admin
def dashboard():
    stats = {
        'notices':         Notice.query.count(),
        'events':          Event.query.count(),
        'gallery_images':  GalleryImage.query.count(),
        'blog_posts':      BlogPost.query.count(),
        'unread_messages': ContactMessage.query.filter_by(is_read=False).count(),
        'downloads':       Download.query.count(),
    }
    recent_messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()
    recent_notices  = Notice.query.order_by(Notice.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats,
                           recent_messages=recent_messages, recent_notices=recent_notices)


# ── Notices ───────────────────────────────────────────────────────────────────

@admin_bp.route('/notices')
@_require_admin
def notices():
    page  = request.args.get('page', 1, type=int)
    q     = request.args.get('q', '')
    query = Notice.query
    if q:
        query = query.filter(Notice.title.ilike(f'%{q}%'))
    pagination = query.order_by(Notice.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/notices.html', pagination=pagination, q=q)


@admin_bp.route('/notices/new', methods=['GET', 'POST'])
@_require_admin
def notice_new():
    form = NoticeForm()
    if form.validate_on_submit():
        attachment = None
        if form.attachment.data and form.attachment.data.filename:
            attachment = save_file(form.attachment.data, 'notices')
        notice = Notice(
            title=form.title.data, content=sanitize_html(form.content.data),
            category=form.category.data, is_pinned=form.is_pinned.data,
            is_published=form.is_published.data, expiry_date=form.expiry_date.data,
            attachment=attachment)
        db.session.add(notice)
        db.session.commit()
        flash('Notice created successfully.', 'success')
        return redirect(url_for('admin.notices'))
    return render_template('admin/notice_form.html', form=form, title='New Notice')


@admin_bp.route('/notices/<int:notice_id>/edit', methods=['GET', 'POST'])
@_require_admin
def notice_edit(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    form   = NoticeForm(obj=notice)
    if form.validate_on_submit():
        if form.attachment.data and form.attachment.data.filename:
            delete_file(notice.attachment, 'notices')
            notice.attachment = save_file(form.attachment.data, 'notices')
        notice.title        = form.title.data
        notice.content      = sanitize_html(form.content.data)
        notice.category     = form.category.data
        notice.is_pinned    = form.is_pinned.data
        notice.is_published = form.is_published.data
        notice.expiry_date  = form.expiry_date.data
        db.session.commit()
        flash('Notice updated.', 'success')
        return redirect(url_for('admin.notices'))
    return render_template('admin/notice_form.html', form=form, notice=notice, title='Edit Notice')


@admin_bp.route('/notices/<int:notice_id>/delete', methods=['POST'])
@_require_admin
def notice_delete(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    delete_file(notice.attachment, 'notices')
    db.session.delete(notice)
    db.session.commit()
    flash('Notice deleted.', 'success')
    return redirect(url_for('admin.notices'))


# ── Events ────────────────────────────────────────────────────────────────────

@admin_bp.route('/events')
@_require_admin
def events():
    page       = request.args.get('page', 1, type=int)
    pagination = Event.query.order_by(Event.event_date.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/events.html', pagination=pagination)


@admin_bp.route('/events/new', methods=['GET', 'POST'])
@_require_admin
def event_new():
    form = EventForm()
    if form.validate_on_submit():
        banner = None
        if form.banner_image.data and form.banner_image.data.filename:
            banner = save_file(form.banner_image.data, 'events', resize=(1200, 600))
        event = Event(
            title=form.title.data, description=sanitize_html(form.description.data),
            location=form.location.data, event_date=form.event_date.data,
            end_date=form.end_date.data, banner_image=banner,
            is_published=form.is_published.data)
        db.session.add(event)
        db.session.commit()
        flash('Event created.', 'success')
        return redirect(url_for('admin.events'))
    return render_template('admin/event_form.html', form=form, title='New Event')


@admin_bp.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@_require_admin
def event_edit(event_id):
    event = Event.query.get_or_404(event_id)
    form  = EventForm(obj=event)
    if form.validate_on_submit():
        if form.banner_image.data and form.banner_image.data.filename:
            delete_file(event.banner_image, 'events')
            event.banner_image = save_file(form.banner_image.data, 'events', resize=(1200, 600))
        event.title        = form.title.data
        event.description  = sanitize_html(form.description.data)
        event.location     = form.location.data
        event.event_date   = form.event_date.data
        event.end_date     = form.end_date.data
        event.is_published = form.is_published.data
        db.session.commit()
        flash('Event updated.', 'success')
        return redirect(url_for('admin.events'))
    return render_template('admin/event_form.html', form=form, event=event, title='Edit Event')


@admin_bp.route('/events/<int:event_id>/delete', methods=['POST'])
@_require_admin
def event_delete(event_id):
    event = Event.query.get_or_404(event_id)
    delete_file(event.banner_image, 'events')
    db.session.delete(event)
    db.session.commit()
    flash('Event deleted.', 'success')
    return redirect(url_for('admin.events'))


# ── Gallery ───────────────────────────────────────────────────────────────────

@admin_bp.route('/gallery')
@_require_admin
def gallery():
    albums = GalleryAlbum.query.order_by(GalleryAlbum.created_at.desc()).all()
    return render_template('admin/gallery.html', albums=albums)


@admin_bp.route('/gallery/albums/new', methods=['GET', 'POST'])
@_require_admin
def album_new():
    form = AlbumForm()
    if form.validate_on_submit():
        album = GalleryAlbum(name=form.name.data, description=form.description.data,
                             is_published=form.is_published.data)
        db.session.add(album)
        db.session.commit()
        flash('Album created.', 'success')
        return redirect(url_for('admin.gallery'))
    return render_template('admin/album_form.html', form=form, title='New Album')


@admin_bp.route('/gallery/albums/<int:album_id>/edit', methods=['GET', 'POST'])
@_require_admin
def album_edit(album_id):
    album = GalleryAlbum.query.get_or_404(album_id)
    form  = AlbumForm(obj=album)
    if form.validate_on_submit():
        album.name         = form.name.data
        album.description  = form.description.data
        album.is_published = form.is_published.data
        db.session.commit()
        flash('Album updated.', 'success')
        return redirect(url_for('admin.gallery'))
    return render_template('admin/album_form.html', form=form, album=album, title='Edit Album')


@admin_bp.route('/gallery/albums/<int:album_id>/delete', methods=['POST'])
@_require_admin
def album_delete(album_id):
    album = GalleryAlbum.query.get_or_404(album_id)
    for img in album.images:
        delete_file(img.filename, 'gallery')
    db.session.delete(album)
    db.session.commit()
    flash('Album and all images deleted.', 'success')
    return redirect(url_for('admin.gallery'))


@admin_bp.route('/gallery/albums/<int:album_id>/images', methods=['GET', 'POST'])
@_require_admin
def album_images(album_id):
    album = GalleryAlbum.query.get_or_404(album_id)
    form  = ImageUploadForm()
    if form.validate_on_submit():
        files = request.files.getlist('images')
        count = 0
        for f in files:
            if f and f.filename and allowed_image(f.filename):
                filename = save_file(f, 'gallery', resize=(1600, 1200))
                if filename:
                    db.session.add(GalleryImage(album_id=album.id, filename=filename))
                    count += 1
        db.session.commit()
        if count:
            first = album.images.order_by(GalleryImage.id.asc()).first()
            if first:
                album.cover_image = first.filename
                db.session.commit()
        flash(f'{count} photo(s) uploaded!', 'success')
        return redirect(url_for('admin.album_images', album_id=album_id))
    images = album.images.order_by(GalleryImage.sort_order.asc()).all()
    return render_template('admin/album_images.html', album=album, images=images, form=form)


@admin_bp.route('/gallery/images/<int:image_id>/delete', methods=['POST'])
@_require_admin
def image_delete(image_id):
    image    = GalleryImage.query.get_or_404(image_id)
    album_id = image.album_id
    delete_file(image.filename, 'gallery')
    db.session.delete(image)
    db.session.commit()
    flash('Image deleted.', 'success')
    return redirect(url_for('admin.album_images', album_id=album_id))


# ── Blog ──────────────────────────────────────────────────────────────────────

@admin_bp.route('/blog')
@_require_admin
def blog():
    page  = request.args.get('page', 1, type=int)
    q     = request.args.get('q', '')
    query = BlogPost.query
    if q:
        query = query.filter(BlogPost.title.ilike(f'%{q}%'))
    pagination = query.order_by(BlogPost.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/blog.html', pagination=pagination, q=q)


@admin_bp.route('/blog/new', methods=['GET', 'POST'])
@_require_admin
def blog_new():
    form = BlogPostForm()
    if form.validate_on_submit():
        base_slug = slugify(form.title.data)
        slug, count = base_slug, 1
        while BlogPost.query.filter_by(slug=slug).first():
            slug = f'{base_slug}-{count}'; count += 1
        image = None
        if form.featured_image.data and form.featured_image.data.filename:
            image = save_file(form.featured_image.data, 'blog', resize=(1200, 630))
        post = BlogPost(
            title=form.title.data, slug=slug, content=sanitize_html(form.content.data),
            excerpt=form.excerpt.data, category=form.category.data,
            featured_image=image, is_published=form.is_published.data,
            is_featured=form.is_featured.data)
        db.session.add(post)
        db.session.commit()
        flash('Post published.', 'success')
        return redirect(url_for('admin.blog'))
    return render_template('admin/blog_form.html', form=form, title='New Post')


@admin_bp.route('/blog/<int:post_id>/edit', methods=['GET', 'POST'])
@_require_admin
def blog_edit(post_id):
    post = BlogPost.query.get_or_404(post_id)
    form = BlogPostForm(obj=post)
    if form.validate_on_submit():
        if form.featured_image.data and form.featured_image.data.filename:
            delete_file(post.featured_image, 'blog')
            post.featured_image = save_file(form.featured_image.data, 'blog', resize=(1200, 630))
        post.title        = form.title.data
        post.content      = sanitize_html(form.content.data)
        post.excerpt      = form.excerpt.data
        post.category     = form.category.data
        post.is_published = form.is_published.data
        post.is_featured  = form.is_featured.data
        db.session.commit()
        flash('Post updated.', 'success')
        return redirect(url_for('admin.blog'))
    return render_template('admin/blog_form.html', form=form, post=post, title='Edit Post')


@admin_bp.route('/blog/<int:post_id>/delete', methods=['POST'])
@_require_admin
def blog_delete(post_id):
    post = BlogPost.query.get_or_404(post_id)
    delete_file(post.featured_image, 'blog')
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted.', 'success')
    return redirect(url_for('admin.blog'))


# ── Messages ──────────────────────────────────────────────────────────────────

@admin_bp.route('/messages')
@_require_admin
def messages():
    page        = request.args.get('page', 1, type=int)
    filter_read = request.args.get('read', '')
    query       = ContactMessage.query
    if filter_read == 'unread':
        query = query.filter_by(is_read=False)
    elif filter_read == 'read':
        query = query.filter_by(is_read=True)
    pagination = query.order_by(ContactMessage.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/messages.html', pagination=pagination, filter_read=filter_read)


@admin_bp.route('/messages/<int:msg_id>')
@_require_admin
def message_view(msg_id):
    msg         = ContactMessage.query.get_or_404(msg_id)
    msg.is_read = True
    db.session.commit()
    return render_template('admin/message_detail.html', msg=msg)


@admin_bp.route('/messages/<int:msg_id>/delete', methods=['POST'])
@_require_admin
def message_delete(msg_id):
    msg = ContactMessage.query.get_or_404(msg_id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted.', 'success')
    return redirect(url_for('admin.messages'))


# ── Downloads ─────────────────────────────────────────────────────────────────

@admin_bp.route('/downloads')
@_require_admin
def downloads():
    page       = request.args.get('page', 1, type=int)
    pagination = Download.query.order_by(Download.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/downloads.html', pagination=pagination)


@admin_bp.route('/downloads/new', methods=['GET', 'POST'])
@_require_admin
def download_new():
    form = DownloadForm()
    if form.validate_on_submit():
        file_obj  = form.file.data
        filename  = save_file(file_obj, 'downloads')
        file_size = None
        if filename and not filename.startswith('http'):
            full_path = os.path.join(app.config['UPLOAD_FOLDER'], 'downloads',
                                     os.path.basename(filename))
            file_size = os.path.getsize(full_path) if os.path.exists(full_path) else None
        dl = Download(
            title=form.title.data, description=form.description.data,
            filename=filename, original_name=file_obj.filename,
            category=form.category.data, file_size=file_size,
            is_published=form.is_published.data)
        db.session.add(dl)
        db.session.commit()
        flash('File uploaded.', 'success')
        return redirect(url_for('admin.downloads'))
    return render_template('admin/download_form.html', form=form, title='Upload File')


@admin_bp.route('/downloads/<int:dl_id>/delete', methods=['POST'])
@_require_admin
def download_delete(dl_id):
    dl = Download.query.get_or_404(dl_id)
    delete_file(dl.filename, 'downloads')
    db.session.delete(dl)
    db.session.commit()
    flash('File deleted.', 'success')
    return redirect(url_for('admin.downloads'))


# ── Homepage Content ──────────────────────────────────────────────────────────

@admin_bp.route('/homepage')
@_require_admin
def homepage():
    sections    = HomepageContent.query.all()
    section_map = {s.section: s for s in sections}
    return render_template('admin/homepage.html', section_map=section_map)


@admin_bp.route('/homepage/hero', methods=['GET', 'POST'])
@_require_admin
def homepage_hero():
    content = HomepageContent.query.filter_by(section='hero').first()
    form    = HomepageHeroForm(obj=content)
    if form.validate_on_submit():
        image = content.image if content else None
        if form.image.data and form.image.data.filename:
            delete_file(image, 'misc')
            image = save_file(form.image.data, 'misc', resize=(1920, 900))
        if not content:
            content = HomepageContent(section='hero')
            db.session.add(content)
        content.title   = form.title.data
        content.subtitle= form.subtitle.data
        content.content = form.content.data
        content.image   = image
        db.session.commit()
        flash('Hero section updated.', 'success')
        return redirect(url_for('admin.homepage'))
    return render_template('admin/homepage_section_form.html', form=form,
                           title='Edit Hero Section', content=content)


@admin_bp.route('/homepage/<section_name>', methods=['GET', 'POST'])
@_require_admin
def homepage_section(section_name):
    allowed = ['about', 'principal', 'mission', 'stats']
    if section_name not in allowed:
        abort(404)
    content = HomepageContent.query.filter_by(section=section_name).first()
    form    = HomepageHeroForm(obj=content)
    titles  = {
        'about':     'Edit About Section',
        'principal': 'Edit Principal Message',
        'mission':   'Edit Mission & Vision',
        'stats':     'Edit School Stats',
    }
    if form.validate_on_submit():
        image = content.image if content else None
        if form.image.data and form.image.data.filename:
            delete_file(image, 'misc')
            image = save_file(form.image.data, 'misc', resize=(1200, 800))
        if not content:
            content = HomepageContent(section=section_name)
            db.session.add(content)
        content.title    = form.title.data
        content.subtitle = form.subtitle.data
        content.content  = form.content.data
        content.image    = image
        db.session.commit()
        flash(f'{titles[section_name]} updated.', 'success')
        return redirect(url_for('admin.homepage'))
    return render_template('admin/homepage_section_form.html', form=form,
                           title=titles[section_name], content=content)


# ── Admin Profile & Settings ──────────────────────────────────────────────────

@admin_bp.route('/profile', methods=['GET', 'POST'])
@_require_admin
def profile():
    form = AdminProfileForm(obj=current_user)
    if form.validate_on_submit():
        existing = Admin.query.filter(
            Admin.email == form.email.data,
            Admin.id != current_user.id
        ).first()
        if existing:
            flash('That email is already in use.', 'danger')
        else:
            current_user.full_name = form.full_name.data
            current_user.email     = form.email.data
            db.session.commit()
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('admin.profile'))
    return render_template('admin/profile.html', form=form)


@admin_bp.route('/settings')
@_require_admin
def settings():
    return render_template('admin/settings.html')


# ── Testimonials ──────────────────────────────────────────────────────────────

@admin_bp.route('/testimonials')
@_require_admin
def testimonials():
    items = Testimonial.query.order_by(Testimonial.sort_order.asc()).all()
    return render_template('admin/testimonials.html', testimonials=items)


@admin_bp.route('/testimonials/new', methods=['GET', 'POST'])
@_require_admin
def testimonial_new():
    form = TestimonialForm()
    if form.validate_on_submit():
        avatar = None
        if form.avatar.data and form.avatar.data.filename:
            avatar = save_file(form.avatar.data, 'misc', resize=(200, 200))
        t = Testimonial(
            name=form.name.data, role=form.role.data,
            content=form.content.data, rating=form.rating.data or 5, avatar=avatar)
        db.session.add(t)
        db.session.commit()
        flash('Testimonial added.', 'success')
        return redirect(url_for('admin.testimonials'))
    return render_template('admin/testimonial_form.html', form=form, title='Add Testimonial')


@admin_bp.route('/testimonials/<int:t_id>/delete', methods=['POST'])
@_require_admin
def testimonial_delete(t_id):
    t = Testimonial.query.get_or_404(t_id)
    delete_file(t.avatar, 'misc')
    db.session.delete(t)
    db.session.commit()
    flash('Testimonial deleted.', 'success')
    return redirect(url_for('admin.testimonials'))


# ── Board of Directors ────────────────────────────────────────────────────────

@admin_bp.route('/board-members')
@_require_admin
def board_members():
    members = BoardMember.query.order_by(BoardMember.sort_order.asc(), BoardMember.name.asc()).all()
    return render_template('admin/board_members.html', members=members)


@admin_bp.route('/board-members/new', methods=['GET', 'POST'])
@_require_admin
def board_member_new():
    form = BoardMemberForm()
    if form.validate_on_submit():
        photo = save_file(form.photo.data, 'board', resize=(600, 600))
        m = BoardMember(
            name=form.name.data, position=form.position.data,
            category=form.category.data,
            bio=bleach.clean(form.bio.data or '', tags=['p','b','i','br','em','strong'], strip=True),
            email=form.email.data, phone=form.phone.data,
            sort_order=form.sort_order.data or 0,
            is_published=form.is_published.data, photo=photo)
        db.session.add(m)
        db.session.commit()
        flash(f'{m.name} added to Board of Directors.', 'success')
        return redirect(url_for('admin.board_members'))
    return render_template('admin/board_member_form.html', form=form, title='Add Member', member=None)


@admin_bp.route('/board-members/<int:m_id>/edit', methods=['GET', 'POST'])
@_require_admin
def board_member_edit(m_id):
    m    = BoardMember.query.get_or_404(m_id)
    form = BoardMemberForm(obj=m)
    if form.validate_on_submit():
        new_photo = save_file(form.photo.data, 'board', resize=(600, 600))
        if new_photo:
            delete_file(m.photo, 'board')
            m.photo = new_photo
        m.name         = form.name.data
        m.position     = form.position.data
        m.category     = form.category.data
        m.bio          = bleach.clean(form.bio.data or '', tags=['p','b','i','br','em','strong'], strip=True)
        m.email        = form.email.data
        m.phone        = form.phone.data
        m.sort_order   = form.sort_order.data or 0
        m.is_published = form.is_published.data
        db.session.commit()
        flash(f'{m.name} updated.', 'success')
        return redirect(url_for('admin.board_members'))
    return render_template('admin/board_member_form.html', form=form, title='Edit Member', member=m)


@admin_bp.route('/board-members/<int:m_id>/delete', methods=['POST'])
@_require_admin
def board_member_delete(m_id):
    m = BoardMember.query.get_or_404(m_id)
    delete_file(m.photo, 'board')
    db.session.delete(m)
    db.session.commit()
    flash(f'{m.name} removed.', 'success')
    return redirect(url_for('admin.board_members'))


# ── Slides ────────────────────────────────────────────────────────────────────

@admin_bp.route('/slides')
@_require_admin
def slides():
    all_slides = Slide.query.order_by(Slide.sort_order.asc(), Slide.id.asc()).all()
    return render_template('admin/slides.html', slides=all_slides)


@admin_bp.route('/slides/new', methods=['GET', 'POST'])
@_require_admin
def slide_new():
    form = SlideForm()
    if form.validate_on_submit():
        if not form.image.data or not form.image.data.filename:
            flash('A slide image is required.', 'danger')
            return render_template('admin/slide_form.html', form=form, title='Add Slide')
        img = save_file(form.image.data, 'misc', resize=(1920, 700))
        s   = Slide(
            title=form.title.data, subtitle=form.subtitle.data,
            image=img, btn_text=form.btn_text.data or 'Learn More',
            btn_url=form.btn_url.data, sort_order=form.sort_order.data or 0,
            is_active=form.is_active.data)
        db.session.add(s)
        db.session.commit()
        flash('Slide added.', 'success')
        return redirect(url_for('admin.slides'))
    return render_template('admin/slide_form.html', form=form, title='Add Slide')


@admin_bp.route('/slides/<int:slide_id>/edit', methods=['GET', 'POST'])
@_require_admin
def slide_edit(slide_id):
    s    = Slide.query.get_or_404(slide_id)
    form = SlideForm(obj=s)
    if form.validate_on_submit():
        img = s.image
        if form.image.data and form.image.data.filename:
            delete_file(img, 'misc')
            img = save_file(form.image.data, 'misc', resize=(1920, 700))
        s.title      = form.title.data
        s.subtitle   = form.subtitle.data
        s.image      = img
        s.btn_text   = form.btn_text.data or 'Learn More'
        s.btn_url    = form.btn_url.data
        s.sort_order = form.sort_order.data or 0
        s.is_active  = form.is_active.data
        db.session.commit()
        flash('Slide updated.', 'success')
        return redirect(url_for('admin.slides'))
    return render_template('admin/slide_form.html', form=form, title='Edit Slide', slide=s)


@admin_bp.route('/slides/<int:slide_id>/delete', methods=['POST'])
@_require_admin
def slide_delete(slide_id):
    s = Slide.query.get_or_404(slide_id)
    delete_file(s.image, 'misc')
    db.session.delete(s)
    db.session.commit()
    flash('Slide deleted.', 'success')
    return redirect(url_for('admin.slides'))


# ── Toppers ───────────────────────────────────────────────────────────────────

STREAM_LABELS = {
    'science_bio':  'Science (With Biology)',
    'science_math': 'Science (Without Bio / Math)',
    'management':   'Management',
    'law':          'Law',
    'arts':         'Arts',
}


@admin_bp.route('/toppers')
@_require_admin
def toppers():
    all_toppers = Topper.query.order_by(Topper.stream, Topper.sort_order, Topper.rank).all()
    return render_template('admin/toppers.html', toppers=all_toppers, stream_labels=STREAM_LABELS)


@admin_bp.route('/toppers/new', methods=['GET', 'POST'])
@_require_admin
def topper_new():
    form = TopperForm()
    if form.validate_on_submit():
        photo = (save_file(form.photo.data, 'toppers', resize=(400, 400))
                 if form.photo.data and form.photo.data.filename else None)
        t = Topper(
            name=form.name.data, stream=form.stream.data,
            percentage=form.percentage.data or None, year=form.year.data,
            rank=form.rank.data or 1, sort_order=form.sort_order.data or 0,
            is_published=form.is_published.data, photo=photo)
        db.session.add(t)
        db.session.commit()
        flash('Topper added.', 'success')
        return redirect(url_for('admin.toppers'))
    return render_template('admin/topper_form.html', form=form, topper=None,
                           stream_labels=STREAM_LABELS)


@admin_bp.route('/toppers/<int:tid>/edit', methods=['GET', 'POST'])
@_require_admin
def topper_edit(tid):
    t    = Topper.query.get_or_404(tid)
    form = TopperForm(obj=t)
    if form.validate_on_submit():
        if form.photo.data and form.photo.data.filename:
            delete_file(t.photo, 'toppers')
            t.photo = save_file(form.photo.data, 'toppers', resize=(400, 400))
        t.name         = form.name.data
        t.stream       = form.stream.data
        t.percentage   = form.percentage.data or None
        t.year         = form.year.data
        t.rank         = form.rank.data or 1
        t.sort_order   = form.sort_order.data or 0
        t.is_published = form.is_published.data
        db.session.commit()
        flash('Topper updated.', 'success')
        return redirect(url_for('admin.toppers'))
    return render_template('admin/topper_form.html', form=form, topper=t,
                           stream_labels=STREAM_LABELS)


@admin_bp.route('/toppers/<int:tid>/delete', methods=['POST'])
@_require_admin
def topper_delete(tid):
    t = Topper.query.get_or_404(tid)
    delete_file(t.photo, 'toppers')
    db.session.delete(t)
    db.session.commit()
    flash('Topper deleted.', 'success')
    return redirect(url_for('admin.toppers'))


# ── Announcement Popup ────────────────────────────────────────────────────────

@admin_bp.route('/homepage/popup', methods=['GET', 'POST'])
@_require_admin
def homepage_popup():
    content = HomepageContent.query.filter_by(section='popup').first()
    form    = AnnouncementPopupForm(obj=content)
    if request.method == 'POST':
        if form.validate_on_submit():
            enabled = request.form.get('popup_enabled') == '1'
            image   = content.image if content else None
            if form.image.data and form.image.data.filename:
                delete_file(image, 'misc')
                image = save_file(form.image.data, 'misc', resize=(900, 700))
            if not content:
                content = HomepageContent(section='popup')
                db.session.add(content)
            content.title      = form.title.data or ''
            content.subtitle   = form.subtitle.data or ''
            content.content    = form.content.data or ''
            content.image      = image
            content.extra_data = {'enabled': enabled}
            db.session.commit()
            flash('Announcement popup updated.', 'success')
            return redirect(url_for('admin.homepage'))
        else:
            for field, errs in form.errors.items():
                for e in errs:
                    flash(f'{field}: {e}', 'danger')
    return render_template('admin/homepage_popup.html', form=form, content=content)


# ── Privacy Policy ────────────────────────────────────────────────────────────

@admin_bp.route('/privacy-policy', methods=['GET', 'POST'])
@_require_admin
def privacy_policy_admin():
    content = HomepageContent.query.filter_by(section='privacy_policy').first()
    if request.method == 'POST':
        body = bleach.clean(
            request.form.get('content', ''),
            tags=['p','h2','h3','h4','ul','ol','li','strong','em','b','i','br','a','blockquote'],
            attributes={'a': ['href', 'target', 'rel']},
            strip=True,
        )
        last_updated = utc_now().strftime('%d %B %Y')
        if content:
            content.content    = body
            content.extra_data = {**(content.extra_data or {}), 'last_updated': last_updated}
        else:
            content = HomepageContent(
                section='privacy_policy', title='Privacy Policy', content=body,
                extra_data={'last_updated': last_updated})
            db.session.add(content)
        db.session.commit()
        flash('Privacy Policy updated successfully.', 'success')
        return redirect(url_for('admin.privacy_policy_admin'))
    return render_template('admin/privacy_policy.html', content=content)


# ── Notifications (unread messages list) ──────────────────────────────────────

@admin_bp.route('/notifications')
@_require_admin
def notifications():
    """Redirect to messages filtered to unread — bell icon target."""
    return redirect(url_for('admin.messages', read='unread'))


# ── Footer Theme ──────────────────────────────────────────────────────────────

@admin_bp.route('/footer-theme', methods=['GET', 'POST'])
@_require_admin
def footer_theme():
    current = FooterTheme.query.first()
    form    = FooterThemeForm(obj=current)
    if form.validate_on_submit():
        if not current:
            current = FooterTheme()
            db.session.add(current)
        current.theme     = form.theme.data
        current.label     = form.label.data or ''
        current.subtext   = form.subtext.data or ''
        current.cta_text  = form.cta_text.data or ''
        current.cta_url   = form.cta_url.data or ''
        current.is_active = form.is_active.data
        if form.image.data and form.image.data.filename:
            if current.image:
                delete_file(current.image, 'misc')
            current.image = save_file(form.image.data, 'misc', resize=(900, 600))
        db.session.commit()
        flash('Footer theme updated.', 'success')
        return redirect(url_for('admin.footer_theme'))
    return render_template('admin/footer_theme.html', form=form, current=current)


# ─────────────────────────────────────────────
# 11. ERROR HANDLERS
# ─────────────────────────────────────────────

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403


@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('errors/500.html'), 500


# ─────────────────────────────────────────────
# 12. REGISTER BLUEPRINTS
# ─────────────────────────────────────────────
app.register_blueprint(public_bp)
app.register_blueprint(auth_bp,  url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')


# ─────────────────────────────────────────────
# 13. FIRST-RUN DB SEED
# ─────────────────────────────────────────────
def seed_database():
    db.create_all()
    print("✓ Database tables ready.")

    # ── Migration: add missing columns to existing tables ──────────────────
    with db.engine.connect() as conn:
        from sqlalchemy import text

        # Add footer_theme.image if missing
        try:
            conn.execute(text(
                "ALTER TABLE footer_theme ADD COLUMN image VARCHAR(500)"
            ))
            conn.commit()
            print("✓ Migration: added footer_theme.image column")
        except Exception:
            conn.rollback()
            pass  # column already exists — fine

    admin = Admin.query.filter_by(username='msuraj24').first()
    if not admin:
        admin = Admin(username='msuraj24', email='msuraj24@tbc.edu.np', full_name='Site Administrator')
        admin.set_password('suraj@123')
        db.session.add(admin)
        print("✓ Default admin created  →  username: msuraj24  |  password: suraj@123")
    else:
        print("  Admin already exists — password unchanged.")

    if not HomepageContent.query.filter_by(section='hero').first():
        db.session.add(HomepageContent(
            section='hero', title='Welcome to Martyrs Memorial +2',
            subtitle='Excellence in Education Since 1990',
            content='A premier institution committed to holistic education and lifelong learning.'))

    if not HomepageContent.query.filter_by(section='about').first():
        db.session.add(HomepageContent(
            section='about', title='A Legacy of Learning',
            content=('Founded in 1990, Martyrs Memorial +2 has grown into a centre of academic '
                     'and co-curricular excellence, shaping thousands of young minds.')))

    if not HomepageContent.query.filter_by(section='principal').first():
        db.session.add(HomepageContent(
            section='principal', title="Principal's Message",
            subtitle='Mr. John Doe, Principal',
            content=('Education is not merely the acquisition of knowledge; it is the cultivation '
                     'of character, curiosity, and compassion. At Martyrs Memorial +2, every child '
                     'is valued, challenged, and inspired to reach their highest potential.')))

    if not Notice.query.first():
        db.session.add(Notice(
            title='Welcome Back — New Academic Year 2025-26',
            content='We are delighted to welcome students back for the new academic year. Classes commence on 1st July 2025.',
            category='academic', is_pinned=True, is_published=True))

    if not Event.query.first():
        db.session.add(Event(
            title='Annual Sports Day 2025',
            description='Join us for an exciting day of athletics, field events, and team sports.',
            location='School Sports Ground',
            event_date=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30),
            is_published=True))

    if not Testimonial.query.first():
        db.session.add(Testimonial(
            name='Mrs. Priya Sharma', role='Parent',
            content='Martyrs Memorial +2 has been incredible for my daughter. The teachers are dedicated and the emphasis on values makes it truly special.',
            rating=5, is_published=True))

    if not Topper.query.first():
        _dummy = [
            # Science Bio
            ('Aarav Sharma',        'science_bio',  '96.75',  1),
            ('Sita Rai',            'science_bio',  '95.50',  2),
            ('Bishnu Thapa',        'science_bio',  '94.25',  3),
            ('Priya Shrestha',      'science_bio',  '93.80',  4),
            ('Rohan Karki',         'science_bio',  '93.10',  5),
            ('Anisha Paudel',       'science_bio',  '92.60',  6),
            ('Dipesh Adhikari',     'science_bio',  '91.90',  7),
            ('Manisha Koirala',     'science_bio',  '91.25',  8),
            ('Sujan Bista',         'science_bio',  '90.75',  9),
            ('Kabita Gurung',       'science_bio',  '90.10', 10),
            # Science Math
            ('Nischal Acharya',     'science_math', '97.20',  1),
            ('Asmita Tamang',       'science_math', '96.40',  2),
            ('Pratik Lama',         'science_math', '95.80',  3),
            ('Sunita Maharjan',     'science_math', '94.60',  4),
            ('Bibek Pandey',        'science_math', '93.75',  5),
            ('Kritika Subedi',      'science_math', '93.00',  6),
            ('Milan Dahal',         'science_math', '92.30',  7),
            ('Rekha Neupane',       'science_math', '91.80',  8),
            ('Sandesh Bhattarai',   'science_math', '91.10',  9),
            ('Puja Sapkota',        'science_math', '90.50', 10),
            # Management
            ('Rajan Pokhrel',       'management',   '95.40',  1),
            ('Samiksha Joshi',      'management',   '94.20',  2),
            ('Nabin Khadka',        'management',   '93.60',  3),
            ('Anjali Magar',        'management',   '92.90',  4),
            ('Sailesh Giri',        'management',   '92.10',  5),
            ('Binita Chaudhary',    'management',   '91.50',  6),
            ('Rohit Yadav',         'management',   '91.00',  7),
            ('Elina Limbu',         'management',   '90.40',  8),
            ('Aakash Basnet',       'management',   '89.80',  9),
            ('Nirmala Rajbhandari', 'management',   '89.20', 10),
            # Law
            ('Bibhuti Prasad',      'law',          '94.80',  1),
            ('Sapana Dhakal',       'law',          '93.50',  2),
            ('Suresh Oli',          'law',          '92.70',  3),
            ('Kopila Tiwari',       'law',          '92.00',  4),
            ('Ujjwal Budhathoki',   'law',          '91.30',  5),
            ('Shreya Baral',        'law',          '90.80',  6),
            ('Dinesh Humagain',     'law',          '90.10',  7),
            ('Rojina Ghimire',      'law',          '89.60',  8),
            ('Shyam Hamal',         'law',          '89.00',  9),
            ('Mina Chand',          'law',          '88.50', 10),
            # Arts
            ('Prabhat Regmi',       'arts',         '93.90',  1),
            ('Srijana Bhandari',    'arts',         '92.60',  2),
            ('Tulasi Pantha',       'arts',         '91.80',  3),
            ('Ramesh Tharu',        'arts',         '91.00',  4),
            ('Laxmi Chhetri',       'arts',         '90.40',  5),
            ('Govind Pariyar',      'arts',         '89.70',  6),
            ('Saraswati Sah',       'arts',         '89.10',  7),
            ('Deepak Rai',          'arts',         '88.60',  8),
            ('Rupa Tamrakar',       'arts',         '88.00',  9),
            ('Janak Upreti',        'arts',         '87.50', 10),
        ]
        for name, stream, pct, rank in _dummy:
            db.session.add(Topper(
                name=name, stream=stream, percentage=pct,
                year='2082', rank=rank, is_published=True, sort_order=rank))
        print(f"  Seeded {len(_dummy)} dummy toppers.")

    # Seed default footer theme row
    if not FooterTheme.query.first():
        db.session.add(FooterTheme(
            theme='default', label='', subtext='', cta_text='', cta_url='', is_active=False))
        print("  Seeded default footer theme.")

    db.session.commit()
    print("✓ Database seed complete.")


# ─────────────────────────────────────────────
# 14. AUTO-INIT ON STARTUP
# ─────────────────────────────────────────────
with app.app_context():
    try:
        seed_database()
    except Exception as _seed_err:
        db.session.rollback()
        print(f"⚠ Seed warning (non-fatal): {_seed_err}")
    finally:
        db.session.remove()


# ─────────────────────────────────────────────
# 15. DEV SERVER
# ─────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5000)