import sys
import os

import zango

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
    "session_security",
    "django_celery_beat",
    "django_celery_results",
    "rest_framework",
    "knox",
    # 'nocaptcha_recaptcha',
    "zango.apps.shared.tenancy",
    "zango.apps.shared.platformauth",
]


TENANT_APPS = [
    # The following Django contrib apps must be in TENANT_APPS
    "django.contrib.contenttypes",
    "zango.apps.appauth",
    "zango.apps.permissions",
    "zango.apps.object_store",
    "zango.apps.dynamic_models",
    "zango.apps.tasks",
    "zango.apps.auditlogs",
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
    "zango.middleware.tenant.ZangoTenantMainMiddleware",
    # 'zango.middleware.context_middleware.SimpleContextMiddleware',
    # 'zango.middleware.tenant_url_switch.url_switch_middleware',
    # 'django_tenants.middleware.main.TenantMainMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "session_security.middleware.SessionSecurityMiddleware",
    "zango.middleware.request.UserRoleAndAppObjectAssignmentMiddleware",
    # 'zango.middleware.middleware.SetUserRoleMiddleWare',
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "zango.middleware.tenant.TimezoneMiddleware",
    "zango.apps.auditlogs.middleware.AuditlogMiddleware",
]


AUTHENTICATION_BACKENDS = (
    "zango.apps.shared.platformauth.auth_backend.PlatformUserModelBackend",
    "zango.apps.appauth.auth_backend.AppUserModelBackend",
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
                "zango.core.template_loader.AppTemplateLoader",
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
STATICFILES_DIRS = [os.path.join(os.path.dirname(zango.__file__), "assets")]


CRISPY_ALLOWED_TEMPLATE_PACKS = (
    "ukcrisp",
    "uni_form",
    "bootstrap5",
)

CRISPY_TEMPLATE_PACK = "bootstrap5"

SESSION_COOKIE_NAME = "zangocookie"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

LOGOUT_REDIRECT_URL = "/auth/login"

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

# Session Security
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SECURITY_WARN_AFTER = 1700
SESSION_SECURITY_EXPIRE_AFTER = 1800

# List of url names that should be ignored by the session security middleware.
# For example the request of history_sidebar is made without user intervention,
# as such it should not be used to update the user’s last activity datetime.
SESSION_SECURITY_PASSIVE_URL_NAMES = [
    "history_sidebar",
]
