import os
from zelthy3.base_settings import *

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = 'django-insecure-)c3(unqe=siu7j&=ew+_o^fec9sujmik*mh4es)v^_&bpiy^b*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]



WSGI_APPLICATION = 'tests.wsgi.application'

INSTALLED_APPS.append("tests")


DATABASES = {
    'default': {
        'ENGINE':'django_tenants.postgresql_backend',
        'NAME': 'postgres24',
        'USER': 'postgres',
        'PASSWORD': 'zelthy3pass',
        'HOST': '127.0.0.1',
        'PORT': '5432',
        # 'ATOMIC_REQUESTS':True
    }
}

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = [
    'http://localhost:8000',
    'https://localhost:8000',
    'http://tenant3.zelthy.com:8000'
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True



STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = 'static/'

import os
TEMPLATES[0]['DIRS'] = [os.path.join(BASE_DIR, 'templates')]

SHOW_PUBLIC_IF_NO_TENANT_FOUND = False

ENV='dev'