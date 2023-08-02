"""
Django settings for treasure project.

Generated by 'django-admin startproject' using Django 2.2.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""
from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Any


# Where is the app being deployed?
class Deployment(Enum):
    LOCAL = 1
    AZURE = 2


deployment_type = Deployment[os.getenv("DEPLOYMENT", "LOCAL")]
local_deploy = deployment_type == Deployment.LOCAL

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = local_deploy

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "insecure" if local_deploy else os.environ["SECRET_KEY"]

ALLOWED_HOSTS = [] if local_deploy else ["www.e-treasure-hunt.com"]
CSRF_TRUSTED_ORIGINS = ["https://www.e-treasure-hunt.com"]

app_url = os.getenv("APP_URL")
if app_url is not None:
    ALLOWED_HOSTS.append(app_url)
    CSRF_TRUSTED_ORIGINS.append(f"https://{app_url}")

# Extra settings from security check
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = not local_deploy
CSRF_COOKIE_SECURE = not local_deploy
X_FRAME_OPTIONS = "DENY"

# Close the session when user closes the browser
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_AGE = 5184000

# Django 3.2 default.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Storage.
BASE_DIR = Path(__file__).parents[1]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

storage_backends = {
    Deployment.AZURE: "storages.backends.azure_storage.AzureStorage",
    Deployment.LOCAL: "django.core.files.storage.FileSystemStorage",
}
STORAGES = {
    "default": {"BACKEND": storage_backends[deployment_type]},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

if deployment_type == Deployment.AZURE:
    from azure.identity import ManagedIdentityCredential

    AZURE_TOKEN_CREDENTIAL = ManagedIdentityCredential()
    AZURE_ACCOUNT_NAME = os.environ["AZURE_ACCOUNT_NAME"]
    AZURE_CONTAINER = os.environ["AZURE_CONTAINER"]
    AZURE_URL_EXPIRATION_SECS = 900

# Application definition
INSTALLED_APPS = [
    "daphne",
    "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "storages",
    "hunt",
    "channels",
]

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

ROOT_URLCONF = "treasure.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "treasure.wsgi.application"
ASGI_APPLICATION = "treasure.asgi.application"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "ERROR"),
        }
    },
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators
PASSWORD_VALIDATION = "django.contrib.auth.password_validation"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": f"{PASSWORD_VALIDATION}.{validator}"}
    for validator in (
        "UserAttributeSimilarityValidator",
        "MinimumLengthValidator",
        "CommonPasswordValidator",
        "NumericPasswordValidator",
    )
]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAdminUser"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

DATABASES: dict[str, Any]
if deployment_type == Deployment.LOCAL:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "treasure.sqlite",
        }
    }
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [("localhost", 6379)],
            },
        },
    }
elif deployment_type == Deployment.AZURE:
    DATABASES = {
        "default": {
            "ENGINE": "mssql",
            "HOST": os.environ["DBHOST"],
            "NAME": os.environ["DBNAME"],
            "Trusted_Connection": "no",
            "OPTIONS": {
                "extra_params": "Authentication=ActiveDirectoryMsi",
            },
        }
    }
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [
                    f"rediss://:{os.environ['CACHEPASSWORD']}@{os.environ['CACHEURL']}:6380/0"
                ],
            },
        },
    }
