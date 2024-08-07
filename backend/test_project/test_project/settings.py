from pathlib import Path
import os
import environ
from datetime import timedelta
import zango
from zango.core.utils import generate_lockout_response

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

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
    "axes",
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
    "zango.apps.accesslogs",
    "corsheaders",
    "crispy_forms",
    "crispy_bootstrap5",
    "debug_toolbar",
    "crispy_forms",
    "django_celery_results",
    # "cachalot",
    "axes",
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
    "axes.middleware.AxesMiddleware",
    "zango.middleware.telemetry.OtelZangoContextMiddleware",
]

AUTHENTICATION_BACKENDS = (
    "axes.backends.AxesStandaloneBackend",
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
                (
                    "django.template.loaders.filesystem.Loader",
                    [os.path.join(os.path.dirname(zango.__file__), "templates")],
                ),
                "django.template.loaders.app_directories.Loader",
            ],
        },
    },
]


DATABASE_ROUTERS = ("django_tenants.routers.TenantSyncRouter",)

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}


MIGRATION_MODULES = {}
RUNNING_ZMAKEMIGRATIONS = False

INTERNAL_IPS = [
    "127.0.0.1",
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

AXES_BEHIND_REVERSE_PROXY = True
AXES_FAILURE_LIMIT = 6
AXES_LOCK_OUT_AT_FAILURE = True
AXES_COOLOFF_TIME = timedelta(seconds=900)

AXES_ENABLED = True
AXES_LOCKOUT_CALLABLE = generate_lockout_response
AXES_LOCKOUT_PARAMETERS = ["ip_address", ["username", "user_agent"]]
AXES_ENABLE_ACCESS_FAILURE_LOG = True
AXES_META_PRECEDENCE_ORDER = (
    "REMOTE_ADDR",
    "HTTP_X_FORWARDED_FOR",
    "HTTP_X_REAL_IP",
)

SHOW_PUBLIC_IF_NO_TENANT_FOUND = False
PUBLIC_SCHEMA_URLCONF = "zango.config.urls_public"


env = environ.Env(
    DEBUG=(bool, True),
    ENV=(str, "dev"),
    SECRET_KEY=(str, ""),
    LANGUAGE_CODE=(str, "en-us"),
    TIME_ZONE=(str, "UTC"),
    USE_I18N=(bool, True),
    USE_TZ=(bool, True),
    REDIS_HOST=(str, "127.0.0.1"),
    REDIS_PORT=(str, "6379"),
    SESSION_SECURITY_WARN_AFTER=(int, 1700),
    SESSION_SECURITY_EXPIRE_AFTER=(int, 1800),
    INTERNAL_IPS=(list, ['127.0.0.1']),
    AXES_BEHIND_REVERSE_PROXY=(bool, False),
    AXES_FAILURE_LIMIT=(int, 6),
    AXES_LOCK_OUT_AT_FAILURE=(bool, True),
    AXES_COOLOFF_TIME=(int, 900),
    PHONENUMBER_DEFAULT_REGION=(str, "IN"),
    PACKAGE_REPO_AWS_ACCESS_KEY_ID=(str, ""),
    PACKAGE_REPO_AWS_SECRET_ACCESS_KEY=(str, ""),
    OTEL_IS_ENABLED=(bool, False),
    OTEL_EXPORT_TO_OTLP=(bool, False),
    OTEL_EXPORTER_OTLP_ENDPOINT=(str, "http://localhost:4317"),
    OTEL_EXPORTER_OTLP_HEADERS=(str, ""),
    OTEL_EXPORTER_PROTOCOL=(str, ""),
    OTEL_RESOURCE_NAME=(str, "Zango"),
)

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

ENV = env("ENV")

SECRET_KEY = "not needed"
DEBUG = True

ALLOWED_HOSTS = [
    "localhost",
    "testserver",
    "other.example.com",
    "127.0.0.1",
    "0.0.0.0",
]
project_name = "test_project"
PROJECT_NAME = project_name

WSGI_APPLICATION = f"{project_name}.wsgi.application"

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

redis_url = (
    f"{REDIS_PROTOCOL}://{REDIS_HOST}:{REDIS_PORT}/1"
)

REDIS_URL = redis_url
CELERY_BROKER_URL = redis_url

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": redis_url,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "TIMEOUT": 300,  # Default timeout is 5 minutes, but adjust as needed
    }
}

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

LANGUAGE_CODE = env("LANGUAGE_CODE")
TIME_ZONE = env("TIME_ZONE")
USE_I18N = env("USE_I18N")
USE_TZ = env("USE_TZ")

TEMPLATES[0]["DIRS"] = [os.path.join(BASE_DIR, "templates")]

ROOT_URLCONF = f"{project_name}.urls_tenants"

PHONENUMBER_DEFAULT_REGION = env("PHONENUMBER_DEFAULT_REGION")

MEDIA_ROOT = os.path.join(BASE_DIR, "zango/tests/media")


STATIC_ROOT = os.path.join(BASE_DIR, "zango/tests/static")
STATICFILES_DIRS += [os.path.join(BASE_DIR, "zango/tests/assets")]

PACKAGE_REPO_AWS_ACCESS_KEY_ID = env("PACKAGE_REPO_AWS_ACCESS_KEY_ID")
PACKAGE_REPO_AWS_SECRET_ACCESS_KEY = env(
    "PACKAGE_REPO_AWS_SECRET_ACCESS_KEY"
)

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

AXES_BEHIND_REVERSE_PROXY = env("AXES_BEHIND_REVERSE_PROXY")
AXES_FAILURE_LIMIT = env("AXES_FAILURE_LIMIT")
AXES_LOCK_OUT_AT_FAILURE = env("AXES_LOCK_OUT_AT_FAILURE")
AXES_COOLOFF_TIME = timedelta(seconds=env("AXES_COOLOFF_TIME"))

# OTEL Settings
OTEL_IS_ENABLED = env("OTEL_IS_ENABLED")
OTEL_EXPORT_TO_OTLP = env("OTEL_EXPORT_TO_OTLP")
OTEL_EXPORTER_OTLP_ENDPOINT = env("OTEL_EXPORTER_OTLP_ENDPOINT")
OTEL_EXPORTER_OTLP_HEADERS = env("OTEL_EXPORTER_OTLP_HEADERS")
OTEL_EXPORTER_PROTOCOL = env("OTEL_EXPORTER_PROTOCOL")
OTEL_RESOURCE_NAME = env("OTEL_RESOURCE_NAME")

if OTEL_IS_ENABLED:
    MIDDLEWARE.append("zango.middleware.telemetry.OtelZangoContextMiddleware")
