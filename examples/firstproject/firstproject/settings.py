
from zelthy3.base_settings import *

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = 'django-insecure-)c3(unqe=siu7j&=ew+_o^fec9sujmik*mh4es)v^_&bpiy^b*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]


ROOT_URLCONF = 'firstproject.urls'

WSGI_APPLICATION = 'firstproject.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE':'django_tenants.postgresql_backend',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'zelthy3pass',
        'HOST': '127.0.0.1',
        'PORT': '5432',
        'ATOMIC_REQUESTS':True
    }
}




# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# ROOT_URLCONF = 'firstproject.urls'

STATIC_URL = 'static/'