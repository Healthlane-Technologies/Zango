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
CORS_ORIGIN_WHITELIST = ["http://localhost:8000"]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# ROOT_URLCONF = '{{project_name}}.urls'
STATICFILES_DIRS = (os.path.join(BASE_DIR, "assets"),)
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATIC_URL = "static/"

import os

TEMPLATES[0]["DIRS"] = [os.path.join(BASE_DIR, "templates")]

SHOW_PUBLIC_IF_NO_TENANT_FOUND = False
PUBLIC_SCHEMA_URLCONF = "zelthy.config.urls_public"
ROOT_URLCONF = "{{project_name}}.urls_tenants"

ENV = "dev"

PHONENUMBER_DEFAULT_REGION = "IN"
