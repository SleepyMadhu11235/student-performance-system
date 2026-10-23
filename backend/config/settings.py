"""
Django settings for the Student Performance Prediction System backend.
"""

import os
import ssl
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "insecure-dev-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("true", "1")

# ALLOWED_HOSTS configuration with Render auto-detection
ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

if os.getenv("DJANGO_ALLOW_ALL_HOSTS", "False").lower() in ("true", "1"):
    ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "predictions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Serve static files efficiently in production
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Helper to resolve relative and absolute paths
# ---------------------------------------------------------------------------

def _resolve(path_str: str) -> Path:
    path = Path(path_str)
    return path if path.is_absolute() else BASE_DIR / path

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# Supports:
# 1. SQLite: DB_ENGINE=sqlite
# 2. Aiven MySQL / Cloud MySQL via individual env vars (DB_HOST, DB_USER, etc.)
# 3. Cloud MySQL via connection string: DATABASE_URL (e.g. mysql://avnadmin:...@...:port/defaultdb)
# 4. Automatic SSL configuration for Aiven MySQL (via ca.pem or verified TLS handshake)

def _build_database_config():
    db_engine = os.getenv("DB_ENGINE", "mysql").lower()
    database_url = os.getenv("DATABASE_URL")

    if db_engine == "sqlite":
        return {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }

    if database_url:
        import dj_database_url
        db_conf = dj_database_url.parse(database_url, engine="django.db.backends.mysql")
    else:
        db_conf = {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME", "defaultdb"),
            "USER": os.getenv("DB_USER", "avnadmin"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "OPTIONS": {},
        }

    if "OPTIONS" not in db_conf:
        db_conf["OPTIONS"] = {}
    db_conf["OPTIONS"]["charset"] = "utf8mb4"

    # Clean up parameters that dj-database-url injects from URL query strings
    # (e.g. ?ssl-mode=REQUIRED), which PyMySQL rejects with TypeError.
    for invalid_opt in ["ssl-mode", "sslmode", "ssl_mode"]:
        db_conf["OPTIONS"].pop(invalid_opt, None)

    ca_from_query = db_conf["OPTIONS"].pop("ssl-ca", None) or db_conf["OPTIONS"].pop("ssl_ca", None)

    # SSL Handling for Aiven / Cloud MySQL
    ssl_disabled = os.getenv("DB_SSL_DISABLED", "False").lower() in ("true", "1")
    host = db_conf.get("HOST", "")
    is_cloud_db = (
        host not in ("127.0.0.1", "localhost", "")
        or "aivencloud.com" in host
        or os.getenv("DB_SSL_REQUIRED", "False").lower() in ("true", "1")
    )

    if not ssl_disabled and is_cloud_db:
        ca_path = None
        # Option 1: Direct CA certificate content provided in an environment variable
        cert_content = os.getenv("DB_SSL_CERT_CONTENT")
        if cert_content and cert_content.strip():
            temp_ca = BASE_DIR / ".aiven-ca.pem"
            try:
                temp_ca.write_text(cert_content.strip(), encoding="utf-8")
                ca_path = str(temp_ca)
            except Exception:
                pass

        # Option 2: Path provided via DB_SSL_CA or standard locations
        if not ca_path and os.getenv("DB_SSL_CA"):
            candidate = _resolve(os.getenv("DB_SSL_CA"))
            if candidate.exists():
                ca_path = str(candidate)

        if not ca_path and ca_from_query and Path(ca_from_query).exists():
            ca_path = str(ca_from_query)

        if not ca_path and (BASE_DIR / "ca.pem").exists():
            ca_path = str(BASE_DIR / "ca.pem")
        elif not ca_path and (BASE_DIR / "certs" / "ca.pem").exists():
            ca_path = str(BASE_DIR / "certs" / "ca.pem")
        elif not ca_path and Path("/etc/secrets/ca.pem").exists():
            ca_path = "/etc/secrets/ca.pem"

        if ca_path:
            db_conf["OPTIONS"]["ssl"] = {
                "ca": ca_path,
                "check_hostname": False,
            }
        else:
            # Fallback TLS: satisfies Aiven's require_secure_transport=ON
            # without requiring a local ca.pem file download.
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            db_conf["OPTIONS"]["ssl"] = ssl_ctx

    return {"default": db_conf}

DATABASES = _build_database_config()

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files (WhiteNoise configuration)
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# CORS & CSRF — Frontend origins allowed to call this API
# ---------------------------------------------------------------------------

CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "False").lower() in ("true", "1")

CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]

# Automatically permit Vercel deployments and preview URLs to avoid CORS blockers
if os.getenv("CORS_ALLOW_VERCEL_PREVIEWS", "True").lower() in ("true", "1"):
    CORS_ALLOWED_ORIGIN_REGEXES = [
        r"^https://.*\.vercel\.app$",
    ]
else:
    CORS_ALLOWED_ORIGIN_REGEXES = []

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]

if RENDER_EXTERNAL_HOSTNAME:
    origin = f"https://{RENDER_EXTERNAL_HOSTNAME}"
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
    "EXCEPTION_HANDLER": "core.exceptions.custom_exception_handler",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}

# ---------------------------------------------------------------------------
# ML pipeline artifact locations
# ---------------------------------------------------------------------------

ML_MODEL_PATH = _resolve(os.getenv("ML_MODEL_PATH", "ml_pipeline/model/student_model.pkl"))
ML_METRICS_PATH = _resolve(os.getenv("ML_METRICS_PATH", "ml_pipeline/model/model_metrics.json"))
ML_DATASET_PATH = _resolve(os.getenv("ML_DATASET_PATH", "ml_pipeline/dataset/student_dataset.csv"))

# ---------------------------------------------------------------------------
# Logging — console always; rotating file handler when writable
# ---------------------------------------------------------------------------

LOGS_DIR = BASE_DIR / "logs"
try:
    LOGS_DIR.mkdir(exist_ok=True)
except Exception:
    pass

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} | {levelname:<8} | {name} | {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "app.log",
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 3,
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "predictions": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
