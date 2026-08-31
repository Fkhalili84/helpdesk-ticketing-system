from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Development fallback only. Use an environment variable outside local development.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-key-not-for-production")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_filters",
    "rest_framework",
    "users",
    "core",
    "tickets",
    "organizations",
    "dashboard",
    "notifications.apps.NotificationsConfig",
    "drf_spectacular",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
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
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "users.User"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": 
        "rest_framework.pagination.PageNumberPagination",

    "PAGE_SIZE": 10,
    "DEFAULT_FILTER_BACKENDS": [
    "django_filters.rest_framework.DjangoFilterBackend",
    "rest_framework.filters.SearchFilter",
    "rest_framework.filters.OrderingFilter",
],
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Helpdesk Ticketing System API",

    "DESCRIPTION": (
        "REST API for a multi-tenant helpdesk "
        "ticketing system."
    ),

    "VERSION": "1.0.0",

    "SERVE_INCLUDE_SCHEMA": False,

    "SERVE_PERMISSIONS": [
        "rest_framework.permissions.AllowAny",
    ],

    "COMPONENT_SPLIT_REQUEST": True,

    "SCHEMA_PATH_PREFIX": r"/api",

    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": True,
        "filter": True,
    },

    "TAGS": [
        {
            "name": "Authentication",
            "description": "JWT authentication endpoints.",
        },
        {
            "name": "Organizations",
            "description": (
                "Organization onboarding and management."
            ),
        },
        {
            "name": "Members",
            "description": (
                "Organization member management."
            ),
        },
        {
            "name": "Tickets",
            "description": (
                "Ticket management endpoints."
            ),
        },
        {
            "name": "Dashboard",
            "description": (
                "Organization dashboard and statistics."
            ),
        },
        {
            "name": "Notifications",
            "description": (
                "User notification endpoints."
            ),
        },
    ],
}
