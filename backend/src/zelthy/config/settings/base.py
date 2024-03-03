import sys
import os

import zelthy

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition


SHARED_APPS = [
    "django_tenants",  # mandatory
    # 'zelthy',
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "crispy_forms",
    "crispy_bootstrap5",
    "debug_toolbar",
    # 'phonenumber_field',
    # 'django_otp',
    # 'django_otp.plugins.otp_static',
    # 'django_otp.plugins.otp_totp',
    # 'axes',
    # 'session_security',
    "django_celery_beat",
    "django_celery_results",
    "rest_framework",
    "knox",
    # 'nocaptcha_recaptcha',
    "zelthy.apps.shared.tenancy",
    "zelthy.apps.shared.platformauth",
]


TENANT_APPS = [
    # The following Django contrib apps must be in TENANT_APPS
    "django.contrib.contenttypes",
    "zelthy.apps.appauth",
    "zelthy.apps.permissions",
    "zelthy.apps.object_store",
    "zelthy.apps.dynamic_models",
    "zelthy.apps.tasks",
    "corsheaders",
    "crispy_forms",
    "crispy_bootstrap5",
    "debug_toolbar",
    "crispy_forms",
    "django_celery_results",
    # "cachalot",
]

INSTALLED_APPS = list(SHARED_APPS) + [
    app for app in TENANT_APPS if app not in SHARED_APPS
]

TENANT_MODEL = "tenancy.TenantModel"
TENANT_DOMAIN_MODEL = "tenancy.Domain"


MIDDLEWARE = [
    "zelthy.middleware.tenant.ZelthyTenantMainMiddleware",
    # 'zelthy.middleware.context_middleware.SimpleContextMiddleware',
    # 'zelthy.middleware.tenant_url_switch.url_switch_middleware',
    # 'django_tenants.middleware.main.TenantMainMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "zelthy.middleware.request.UserRoleAndAppObjectAssignmentMiddleware",
    # 'zelthy.middleware.middleware.SetUserRoleMiddleWare',
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "zelthy.middleware.tenant.TimezoneMiddleware",
]


AUTHENTICATION_BACKENDS = (
    "zelthy.apps.shared.platformauth.auth_backend.PlatformUserModelBackend",
    "zelthy.apps.appauth.auth_backend.AppUserModelBackend",
)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": False,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
            # 'builtins': [
            #     'django.contrib.staticfiles',  # Add this line
            # ],
            "loaders": [
                "zelthy.core.template_loader.AppTemplateLoader",
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
        },
    },
]


DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

MIGRATION_MODULES = {}
RUNNING_ZMAKEMIGRATIONS = False

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

# DEBUG_TOOLBAR_PANELS += ['cachalot.panels.CachalotPanel',]

CACHALOT_ENABLED = False

STATIC_URL = "static/"
STATICFILES_DIRS = [os.path.join(os.path.dirname(zelthy.__file__), "assets")]


CRISPY_ALLOWED_TEMPLATE_PACKS = (
    "ukcrisp",
    "uni_form",
    "bootstrap5",
)

CRISPY_TEMPLATE_PACK = "bootstrap5"

SESSION_COOKIE_NAME = "zelthycookie"
SESSION_COOKIE_SECURE = False  # To be changed for prod settings
CSRF_COOKIE_SECURE = False  # To be changed for prod settings

LOGOUT_REDIRECT_URL = "/admin/login"

PASSWORD_MIN_LENGTH = 8
PASSWORD_NO_REPEAT_DAYS = 180
PASSWORD_RESET_DAYS = 90

PACKAGE_REPO_AWS_ACCESS_KEY_ID = os.getenv("PACKAGE_REPO_AWS_ACCESS_KEY_ID")
PACKAGE_REPO_AWS_SECRET_ACCESS_KEY = os.getenv("PACKAGE_REPO_AWS_SECRET_ACCESS_KEY")
MEDIA_URL = "/media/"

# Celery
CELERY_RESULT_BACKEND = "django-db"
X_FRAME_OPTIONS = "ALLOW"

PACKAGE_BUCKET_NAME = "zelthy3-packages"
CODEASSIST_ENABLED = True
