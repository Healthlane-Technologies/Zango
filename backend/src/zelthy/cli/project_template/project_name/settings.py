import os
from zelthy.config.settings.base import *

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = "{{secret_key}}"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]


WSGI_APPLICATION = "{{project_name}}.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django_tenants.postgresql_backend",
        "NAME": "{db_name}",
        "USER": "{db_user}",
        "PASSWORD": "{db_password}",
        "HOST": "{db_host}",
        "PORT": "{db_port}",
        "ATOMIC_REQUESTS": True,
    }
}

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = [
    "http://localhost:8000"
]  # Change according to domain configured
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:1443"
]  # Change according to domain configured

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
PUBLIC_SCHEMA_URLCONF = "zelthy.config.urls_public"
ROOT_URLCONF = "{{project_name}}.urls_tenants"

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
#     "default": {"BACKEND": "zelthy.core.storage_utils.S3MediaStorage"},
#     "staticfiles": {"BACKEND": "zelthy.core.storage_utils.S3StaticStorage"},
# }
#
AWS_MEDIA_STORAGE_BUCKET_NAME = "AWS_MEDIA_STORAGE_BUCKET_NAME"  # S3 Bucket Name
AWS_MEDIA_STORAGE_LOCATION = (
    "AWS_MEDIA_STORAGE_LOCATION"  # Prefix added to all the files uploaded
)
AWS_STATIC_STORAGE_BUCKET_NAME = "AWS_STATIC_STORAGE_BUCKET_NAME"  # S3 Bucket Name
AWS_STATIC_STORAGE_LOCATION = (
    "AWS_MEDIA_STORAGE_LOCATION"  # Prefix added to all the files uploaded
)

STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "static/"
STATICFILES_DIRS += [os.path.join(BASE_DIR, "assets")]

REDIS_URL = "redis://{redis_host}:6379/1"
CELERY_BROKER_URL = REDIS_URL
