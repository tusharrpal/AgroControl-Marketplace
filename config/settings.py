"""
Django settings for config project.
"""

from pathlib import Path
import os

import dj_database_url
from dotenv import load_dotenv

# --------------------------------------------------
# Paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

# --------------------------------------------------
# Security
# --------------------------------------------------

SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-wfon!hh1dbd*33j%x!t&jqhqzjnkt41&bf8&zzx07%1v8r2fez",
)

DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost",
).split(",")

CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "http://127.0.0.1,http://localhost",
).split(",")

SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False") == "True"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False") == "True"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "False") == "True"
SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "False") == "True"
SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "False") == "True"

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --------------------------------------------------
# Applications
# --------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "users",
    "marketplace",
    "orders",
    "cart",
]

# --------------------------------------------------
# Middleware
# --------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --------------------------------------------------
# URLs
# --------------------------------------------------

ROOT_URLCONF = "config.urls"

# --------------------------------------------------
# Templates
# --------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "cart.context_processors.cart_summary",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --------------------------------------------------
# Database
# --------------------------------------------------

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# --------------------------------------------------
# Password Validation
# --------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# --------------------------------------------------
# Internationalization
# --------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# --------------------------------------------------
# Static Files
# --------------------------------------------------

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# --------------------------------------------------
# Media Files
# --------------------------------------------------

MEDIA_URL = "/media/"

MEDIA_ROOT = BASE_DIR / "media"

# --------------------------------------------------
# Default Primary Key
# --------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --------------------------------------------------
# Custom User Model
# --------------------------------------------------

AUTH_USER_MODEL = "users.User"

LOGIN_URL = "login"