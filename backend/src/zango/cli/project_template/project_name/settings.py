import os
from pathlib import Path
import environ

from zango.config.settings.base import *

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, True),
    REDIS_HOST=(str, "127.0.0.1"),
    REDIS_PORT=(str, "6379"),
    SESSION_SECURITY_WARN_AFTER=(int, 1700),
    SESSION_SECURITY_EXPIRE_AFTER=(int, 1800),
    INTERNAL_IPS=(list, []),
    ALLOWED_HOSTS=(list, ["*"]),
    CORS_ORIGIN_WHITELIST=(list, ["http://localhost:1443", "http://localhost:8000"]),
    CSRF_TRUSTED_ORIGINS=(list, ["http://localhost:1443", "http://localhost:8000"]),
)
environ.Env.read_env(os.path.join(BASE_DIR.parent, ".env"))

SECRET_KEY = "{{secret_key}}"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = env("ALLOWED_HOSTS")

PROJECT_NAME = env("PROJECT_NAME")

WSGI_APPLICATION = f"{PROJECT_NAME}.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST"),
        "PORT": env("POSTGRES_PORT"),
        "ATOMIC_REQUESTS": True,
    }
}

REDIS_HOST = env("REDIS_HOST")
REDIS_PORT = env("REDIS_PORT")
REDIS_PROTOCOL = "redis"

REDIS_URL = f"{REDIS_PROTOCOL}://{REDIS_HOST}:{REDIS_PORT}/1"
CELERY_BROKER_URL = REDIS_URL

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,  # Using DB 1 for cache
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "TIMEOUT": 300,  # Default timeout is 5 minutes, but adjust as needed
    }
}

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = env(
    "CORS_ORIGIN_WHITELIST"
)  # Change according to domain configured
CSRF_TRUSTED_ORIGINS = env(
    "CSRF_TRUSTED_ORIGINS"
)  # Change according to domain configured

# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# ROOT_URLCONF = '{{project_name}}.urls'

import os

TEMPLATES[0]["DIRS"] = [os.path.join(BASE_DIR, "templates")]

SHOW_PUBLIC_IF_NO_TENANT_FOUND = False
PUBLIC_SCHEMA_URLCONF = "zango.config.urls_public"
ROOT_URLCONF = f"{PROJECT_NAME}.urls_tenants"

ENV = "dev"

PHONENUMBER_DEFAULT_REGION = "IN"

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

AWS_ACCESS_KEY_ID = "AWS_ACCESS_KEY_ID"
AWS_SECRET_ACCESS_KEY = "AWS_SECRET_ACCESS_KEY"
AWS_S3_REGION_NAME = "AWS_S3_REGION_NAME"

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# To change the media storage to S3 you can use the BACKEND class provided by the default storage
# To change the static storage to S3 you can use the BACKEND class provided by the staticfiles storage
# STORAGES = {
#     "default": {"BACKEND": "zango.core.storage_utils.S3MediaStorage"},
#     "staticfiles": {"BACKEND": "zango.core.storage_utils.S3StaticStorage"},
# }
#
AWS_MEDIA_STORAGE_BUCKET_NAME = "media"  # S3 Bucket Name
AWS_MEDIA_STORAGE_LOCATION = "media"  # Prefix added to all the files uploaded
AWS_STATIC_STORAGE_BUCKET_NAME = "static"  # S3 Bucket Name
AWS_STATIC_STORAGE_LOCATION = "static"  # Prefix added to all the files uploaded

STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "static/"
STATICFILES_DIRS += [os.path.join(BASE_DIR, "assets")]

# Session Security
SESSION_SECURITY_WARN_AFTER = env("SESSION_SECURITY_WARN_AFTER")
SESSION_SECURITY_EXPIRE_AFTER = env("SESSION_SECURITY_EXPIRE_AFTER")

if DEBUG or ENV == "dev":
    # Disable secure cookies in development or debugging environments
    # to simplify troubleshooting and testing.
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# INTERNAL_IPS can contain a list of IP addresses or CIDR blocks that are considered internal.
# Both individual IP addresses and CIDR notation (e.g., '192.168.1.1' or '192.168.1.0/24') can be provided.
INTERNAL_IPS = env("INTERNAL_IPS")
