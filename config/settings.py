"""Django settings for the "Atraquen el barco" project.

Values that change between environments (secret key, debug, database...) are
read from environment variables or a local `.env` file via django-environ.
See `.env.example` for the available variables.
"""

import sys
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

# Render tells each web service its public address; accept it automatically.
RENDER_EXTERNAL_HOSTNAME = env("RENDER_EXTERNAL_HOSTNAME", default=None)
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

TESTING = "pytest" in sys.modules


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_htmx",
    "django_tailwind_cli",
    "game",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

# The debug toolbar is a dev-only dependency: enable it only when debugging
# locally, never in tests or production (where it isn't installed).
if DEBUG and not TESTING:
    INSTALLED_APPS.append("debug_toolbar")
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]

ROOT_URLCONF = "config.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database: SQLite by default, PostgreSQL in production via DATABASE_URL.

DATABASES = {
    "default": env.db("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
}
# Reuse database connections for a while instead of opening one per request, and check
# they are still alive first (a free cloud database may close idle connections).
DATABASES["default"]["CONN_MAX_AGE"] = 600
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization

LANGUAGE_CODE = "es-es"
TIME_ZONE = "Europe/Madrid"
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "assets"]
# collectstatic gathers every static file here for WhiteNoise to serve in production.
STATIC_ROOT = BASE_DIR / "staticfiles"

# In production WhiteNoise serves the static files (CSS, JS, fonts), right after the
# security middleware. File names get a fingerprint of their content
# (tailwind.4f2a1c.css) and are compressed: when a file changes its name changes too,
# so browsers never use an old cached copy (no more Ctrl+F5). Locally and in tests,
# Django serves them by itself with plain names, which is simpler.
if not DEBUG and not TESTING:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }

# django-tailwind-cli compiles tailwind/source.css into the first STATICFILES_DIRS.
# The source must live outside the static dirs so collectstatic doesn't ship it.
TAILWIND_CLI_SRC_CSS = "tailwind/source.css"
TAILWIND_CLI_DIST_CSS = "css/tailwind.css"


# Email

MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}


# Security in production: HTTPS only, secure cookies. Render's proxy handles HTTPS and
# tells Django about it with the X-Forwarded-Proto header.
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30  # browsers remember "HTTPS only" for 30 days
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False  # onrender.com is not our domain

# Checks from `manage.py check --deploy` that don't apply here, on purpose:
SILENCED_SYSTEM_CHECKS = [
    "mail.E001",  # the game never sends email
    "security.W005",  # HSTS for subdomains: only makes sense with a domain of our own
    "security.W021",  # HSTS preload list: same, needs our own domain
]
