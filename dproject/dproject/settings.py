import os
# from zelthy.config.settings.base import *

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = 'django-insecure-)c3(unqe=siu7j&=ew+_o^fec9sujmik*mh4es)v^_&bpiy^b*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

MIDDLEWARE = [
    # 'zelthy.middleware.tenant.ZelthyTenantMainMiddleware',    
    'django_tenants.middleware.main.TenantMainMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',    
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'zelthy.middleware.middleware.SetUserRoleMiddleWare',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

SHARED_APPS = [
    'django_tenants',  # mandatory
    # 'zelthy',
    
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    # 'phonenumber_field',
    # 'django_otp',
    # 'django_otp.plugins.otp_static',
    # 'django_otp.plugins.otp_totp',
    # 'axes',
    # 'session_security',
    # 'django_celery_beat',
    # 'django_celery_results',
    'rest_framework',
    'knox',
    'tenancy'
    # 'nocaptcha_recaptcha',
    # 'zelthy.apps.shared.tenancy',
    # 'zelthy.apps.shared.platformauth',
     
]


TENANT_APPS = [
    # The following Django contrib apps must be in TENANT_APPS
    'django.contrib.contenttypes',
    # 'zelthy.apps.appauth',
    # 'zelthy.apps.permissions',
    # 'zelthy.apps.dynamic_models',
    'corsheaders',

]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]



WSGI_APPLICATION = 'dproject.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE':'django_tenants.postgresql_backend',
        'NAME': 'zelthy1',
        'USER': 'postgres',
        'PASSWORD': 'zelthy3pass',
        'HOST': 'postgres',
        'PORT': '5432',
        'ATOMIC_REQUESTS':True
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


ROOT_URLCONF = 'dproject.urls'
STATICFILES_DIRS = (
     os.path.join(BASE_DIR, 'assets'),
 )
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = 'static/'

import os
# TEMPLATES[0]['DIRS'] = [os.path.join(BASE_DIR, 'templates')]

SHOW_PUBLIC_IF_NO_TENANT_FOUND = False
PUBLIC_SCHEMA_URLCONF = 'dproject.urls_public'
ROOT_URLCONF = 'dproject.urls_tenants'

ENV='dev'

TENANT_MODEL = "tenancy.TenantModel"
TENANT_DOMAIN_MODEL = "tenancy.Domain"

DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)
# import os
# import importlib
# import sys
# import sys
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler

# class FileChangeHandler(FileSystemEventHandler):
#     def on_modified(self, event):
#         print(f'File {event.src_path} has been modified')
#         if event.src_path.endswith('.py'):
#             module_name = os.path.basename(event.src_path)[:-3]  # Remove ".py" from the end
#             if module_name in sys.modules:
#                 print(f'Reloading module {module_name}')
#                 importlib.reload(sys.modules[module_name])

# # Directory you want to watch for changes
# path_to_watch = os.getcwd()  # this will watch the current working directory
# event_handler = FileChangeHandler()

# observer = Observer()
# observer.schedule(event_handler, path_to_watch, recursive=True)

# observer.start()
# import time
# try:
#     while True:
#         time.sleep(1)
#         print("h")
# except KeyboardInterrupt:
#     observer.stop()

# observer.join()



TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': False,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            # 'builtins': [
            #     'django.contrib.staticfiles',  # Add this line
            # ],           
            'loaders': [
                # 'zelthy.template_loader.AppTemplateLoader',
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',                                             
            ]
        },
    },
]


