import os

from datetime import timedelta

import environ

from celery.schedules import crontab

import zango
import zango.apps.tasks.tasks  # noqa

from zango.core.utils import generate_lockout_response


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
    "axes",
    "session_security",
    "django_celery_beat",
    "django_celery_results",
    "rest_framework",
    "knox",
    "django_recaptcha",
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
    "zango.apps.release",
    "zango.apps.secrets",
    "corsheaders",
    "crispy_forms",
    "crispy_bootstrap5",
    "debug_toolbar",
    "crispy_forms",
    "django_celery_results",
    # "cachalot",
    "axes",
    "django_recaptcha",
    "allauth",
    "allauth.account",
    "allauth.headless",
    "allauth.mfa",
    "allauth.usersessions",
    "django.contrib.humanize",
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
    "zango.middleware.token.TokenMiddleware",
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
    "allauth.account.middleware.AccountMiddleware",
    "allauth.usersessions.middleware.UserSessionsMiddleware",
]

AUTHENTICATION_BACKENDS = (
    "axes.backends.AxesStandaloneBackend",
    "zango.apps.shared.platformauth.auth_backend.PlatformUserModelBackend",
    "zango.apps.appauth.auth_backend.AppUserModelBackend",
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "zango.apps.appauth.auth_backend.KnoxTokenAuthBackend",
    ),
}

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


MEDIA_URL = "/media/"

# Celery
CELERY_RESULT_BACKEND = "django-db"
CELERY_RESULT_EXTENDED = True
CELERY_BEAT_SCHEDULE = {
    "health_check_periodic_task": {
        "task": "zango.apps.tasks.tasks.health_check_periodic_task",
        "schedule": crontab(minute="*/1"),
    },
    "health_check_task": {
        "task": "zango.apps.tasks.tasks.health_check",
        "schedule": crontab(minute="*/1"),
        "enabled": False,
    },
}

X_FRAME_OPTIONS = "ALLOW"

PACKAGE_BUCKET_NAME = "zelthy3-packages"

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

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(app_name)s:%(domain_url)s][%(asctime)s] %(levelname)s [%(pathname)s:%(funcName)s:%(lineno)s] %(message)s %(exc_traceback_content)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "console": {
            "format": "%(levelname)s %(asctime)s %(name)s.%(funcName)s:%(lineno)s- %("
            "message)s "
        },
    },
    "filters": {
        "tenant_filter": {
            "()": "zango.core.monitoring.log_filter.TenantContextFilter",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}

SHOW_PUBLIC_IF_NO_TENANT_FOUND = False
PUBLIC_SCHEMA_URLCONF = "zango.config.urls_public"


AWS_MEDIA_STORAGE_LOCATION = "media"  # Prefix added to all the files uploaded
AWS_STATIC_STORAGE_LOCATION = "static"  # Prefix added to all the files uploaded

TENANT_LIMIT_SET_CALLS = True

ACCOUNT_RATE_LIMITS = {"login_failed": False}
ACCOUNT_LOGIN_BY_CODE_MAX_ATTEMPTS = float("inf")


def setup_settings(settings, BASE_DIR):
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
        INTERNAL_IPS=(list, []),
        ALLOWED_HOSTS=(list, ["*"]),
        CORS_ORIGIN_WHITELIST=(
            list,
            ["http://localhost:1443", "http://localhost:8000"],
        ),
        CSRF_TRUSTED_ORIGINS=(list, ["http://localhost:1443", "http://localhost:8000"]),
        AXES_BEHIND_REVERSE_PROXY=(bool, False),
        AXES_FAILURE_LIMIT=(int, 6),
        AXES_LOCK_OUT_AT_FAILURE=(bool, True),
        AXES_COOLOFF_TIME=(int, 900),
        PHONENUMBER_DEFAULT_REGION=(str, "IN"),
        AWS_MEDIA_STORAGE_BUCKET_NAME=(str, ""),
        AWS_STATIC_STORAGE_BUCKET_NAME=(str, ""),
        AWS_ACCESS_KEY_ID=(str, ""),
        AWS_SECRET_ACCESS_KEY=(str, ""),
        AWS_S3_REGION_NAME=(str, ""),
        PACKAGE_REPO_AWS_ACCESS_KEY_ID=(str, ""),
        PACKAGE_REPO_AWS_SECRET_ACCESS_KEY=(str, ""),
        OTEL_IS_ENABLED=(bool, False),
        OTEL_EXPORT_TO_OTLP=(bool, False),
        OTEL_EXPORTER_OTLP_ENDPOINT=(str, "http://localhost:4317"),
        OTEL_EXPORTER_OTLP_HEADERS=(str, ""),
        OTEL_EXPORTER_PROTOCOL=(str, ""),
        OTEL_RESOURCE_NAME=(str, "Zango"),
        OTEL_COLLECTOR=(bool, True),
        GIT_USERNAME=(str, ""),
        GIT_PASSWORD=(str, ""),
        PLATFORM_AUTH_OIDC_ENABLE=(bool, False),
        GOOGLE_OIDC_CLIENT_ID=(str, ""),
        GOOGLE_OIDC_CLIENT_SECRET=(str, ""),
        GOOGLE_OIDC_ENABLE=(bool, False),
        AZURE_OIDC_CLIENT_ID=(str, ""),
        AZURE_OIDC_CLIENT_SECRET=(str, ""),
        AZURE_OIDC_ENABLE=(bool, False),
        FIELD_ENCRYPTION_KEY=(str, ""),
        ZANGO_TOKEN_TTL=(int, 86400),
        PASSWORD_RECOVERY_TOKEN_EXPIRY=(int, 3600 * 2),
        PASSWORD_RECOVERY_TIME_MESSAGE=(str, "2 hours"),
        PASSWORD_RECOVERY_SALT=(str, "recover-password"),
        RECAPTCHA_PUBLIC_KEY=(str, ""),
        RECAPTCHA_PRIVATE_KEY=(str, ""),
        HEALTH_CHECK_URL=(str, ""),
        MEDIA_STORAGE_BACKEND=(str, "django.core.files.storage.FileSystemStorage"),
        STATIC_STORAGE_BACKEND=(
            str,
            "django.contrib.staticfiles.storage.StaticFilesStorage",
        ),
        SECURE_PROXY_SSL_HEADER=(list, []),
        SENTRY_DSN=(str, ""),
        AWS_CLOUDFRONT_DOMAIN=(str, ""),
    )
    environ.Env.read_env(os.path.join(BASE_DIR.parent, ".env"))

    settings.ENV = env("ENV")

    settings.SECRET_KEY = env("SECRET_KEY")
    settings.DEBUG = env("DEBUG")

    settings.ALLOWED_HOSTS = env("ALLOWED_HOSTS")
    project_name = env("PROJECT_NAME")
    settings.PROJECT_NAME = project_name

    settings.WSGI_APPLICATION = f"{project_name}.wsgi.application"

    settings.DATABASES = {
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

    settings.REDIS_HOST = env("REDIS_HOST")
    settings.REDIS_PORT = env("REDIS_PORT")
    settings.REDIS_PROTOCOL = "redis"

    redis_url = (
        f"{settings.REDIS_PROTOCOL}://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1"
    )

    settings.REDIS_URL = redis_url
    settings.CELERY_BROKER_URL = redis_url

    settings.CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": redis_url,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "TIMEOUT": 300,  # Default timeout is 5 minutes, but adjust as needed
        }
    }

    settings.CORS_ORIGIN_ALLOW_ALL = True
    settings.CORS_ALLOW_ALL_ORIGINS = True
    settings.CORS_ALLOW_CREDENTIALS = True
    settings.CORS_ORIGIN_WHITELIST = env(
        "CORS_ORIGIN_WHITELIST"
    )  # Change according to domain configured
    settings.CSRF_TRUSTED_ORIGINS = env(
        "CSRF_TRUSTED_ORIGINS"
    )  # Change according to domain configured

    settings.LANGUAGE_CODE = env("LANGUAGE_CODE")
    settings.TIME_ZONE = env("TIME_ZONE")
    settings.USE_I18N = env("USE_I18N")
    settings.USE_TZ = env("USE_TZ")

    settings.TEMPLATES[0]["DIRS"] = [os.path.join(BASE_DIR, "templates")]

    settings.ROOT_URLCONF = f"{project_name}.urls_tenants"

    settings.PHONENUMBER_DEFAULT_REGION = env("PHONENUMBER_DEFAULT_REGION")

    settings.MEDIA_ROOT = os.path.join(BASE_DIR, "media")

    settings.AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    settings.AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    settings.AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME")

    settings.AWS_MEDIA_STORAGE_BUCKET_NAME = env("AWS_MEDIA_STORAGE_BUCKET_NAME")
    settings.AWS_STATIC_STORAGE_BUCKET_NAME = env("AWS_STATIC_STORAGE_BUCKET_NAME")

    settings.STATIC_ROOT = os.path.join(BASE_DIR, "static")
    settings.STATICFILES_DIRS += [os.path.join(BASE_DIR, "assets")]

    settings.PACKAGE_REPO_AWS_ACCESS_KEY_ID = env("PACKAGE_REPO_AWS_ACCESS_KEY_ID")
    settings.PACKAGE_REPO_AWS_SECRET_ACCESS_KEY = env(
        "PACKAGE_REPO_AWS_SECRET_ACCESS_KEY"
    )

    # Session Security
    settings.SESSION_SECURITY_WARN_AFTER = env("SESSION_SECURITY_WARN_AFTER")
    settings.SESSION_SECURITY_EXPIRE_AFTER = env("SESSION_SECURITY_EXPIRE_AFTER")

    if settings.DEBUG or settings.ENV == "dev":
        # Disable secure cookies in development or debugging environments
        # to simplify troubleshooting and testing.
        settings.SESSION_COOKIE_SECURE = False
        settings.CSRF_COOKIE_SECURE = False

    # INTERNAL_IPS can contain a list of IP addresses or CIDR blocks that are considered internal.
    # Both individual IP addresses and CIDR notation (e.g., '192.168.1.1' or '192.168.1.0/24') can be provided.
    settings.INTERNAL_IPS = env("INTERNAL_IPS")

    settings.AXES_BEHIND_REVERSE_PROXY = env("AXES_BEHIND_REVERSE_PROXY")
    settings.AXES_FAILURE_LIMIT = env("AXES_FAILURE_LIMIT")
    settings.AXES_LOCK_OUT_AT_FAILURE = env("AXES_LOCK_OUT_AT_FAILURE")
    settings.AXES_COOLOFF_TIME = timedelta(seconds=env("AXES_COOLOFF_TIME"))

    settings.REST_KNOX = {
        "TOKEN_TTL": None
        if env("ZANGO_TOKEN_TTL") == 0
        else timedelta(seconds=env("ZANGO_TOKEN_TTL")),
        "AUTH_HEADER_PREFIX": "Bearer",
    }

    settings.STORAGES = {
        "default": {"BACKEND": env("MEDIA_STORAGE_BACKEND")},
        "staticfiles": {"BACKEND": env("STATIC_STORAGE_BACKEND")},
    }

    log_folder = os.path.join(BASE_DIR, "log")
    log_file = os.path.join(log_folder, "zango.log")

    # Check if the log folder exists, if not, create it
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    # Check if the log file exists, if not, create it
    if not os.path.exists(log_file):
        with open(log_file, "a"):
            pass  # Create an empty file

    settings.LOGGING["handlers"]["file"] = {
        "level": "INFO",
        "class": "logging.handlers.RotatingFileHandler",
        "filename": log_file,
        "maxBytes": 1024 * 1024 * 5,  # 5 MB
        "formatter": "verbose",  # Use the custom formatter
        "filters": ["tenant_filter"],
    }
    settings.LOGGING["loggers"]["django"] = {
        "handlers": ["file"],
        "level": "DEBUG",
        "propagate": True,
    }
    # OTEL Settings
    settings.OTEL_IS_ENABLED = env("OTEL_IS_ENABLED")
    settings.OTEL_EXPORT_TO_OTLP = env("OTEL_EXPORT_TO_OTLP")
    settings.OTEL_EXPORTER_OTLP_ENDPOINT = env("OTEL_EXPORTER_OTLP_ENDPOINT")
    settings.OTEL_EXPORTER_OTLP_HEADERS = env("OTEL_EXPORTER_OTLP_HEADERS")
    settings.OTEL_EXPORTER_PROTOCOL = env("OTEL_EXPORTER_PROTOCOL")
    settings.OTEL_RESOURCE_NAME = env("OTEL_RESOURCE_NAME")
    settings.OTEL_COLLECTOR = env("OTEL_COLLECTOR")

    if settings.OTEL_IS_ENABLED:
        MIDDLEWARE.append("zango.middleware.telemetry.OtelZangoContextMiddleware")

    # Git Settings
    settings.GIT_USERNAME = env("GIT_USERNAME")
    settings.GIT_PASSWORD = env("GIT_PASSWORD")

    settings.PLATFORM_AUTH_OIDC_ENABLE = env("PLATFORM_AUTH_OIDC_ENABLE")
    settings.GOOGLE_OIDC_CLIENT_ID = env("GOOGLE_OIDC_CLIENT_ID")
    settings.GOOGLE_OIDC_CLIENT_SECRET = env("GOOGLE_OIDC_CLIENT_SECRET")
    settings.GOOGLE_OIDC_ENABLE = env("GOOGLE_OIDC_ENABLE")
    settings.AZURE_OIDC_CLIENT_ID = env("AZURE_OIDC_CLIENT_ID")
    settings.AZURE_OIDC_CLIENT_SECRET = env("AZURE_OIDC_CLIENT_SECRET")
    settings.AZURE_OIDC_ENABLE = env("AZURE_OIDC_ENABLE")

    settings.FIELD_ENCRYPTION_KEY = env("FIELD_ENCRYPTION_KEY")

    settings.PASSWORD_RECOVERY_TOKEN_EXPIRY = env("PASSWORD_RECOVERY_TOKEN_EXPIRY")
    settings.PASSWORD_RECOVERY_TIME_MESSAGE = env("PASSWORD_RECOVERY_TIME_MESSAGE")
    settings.PASSWORD_RECOVERY_SALT = env("PASSWORD_RECOVERY_SALT")

    settings.RECAPTCHA_PUBLIC_KEY = env("RECAPTCHA_PUBLIC_KEY")
    settings.RECAPTCHA_PRIVATE_KEY = env("RECAPTCHA_PRIVATE_KEY")

    settings.HEALTH_CHECK_URL = env("HEALTH_CHECK_URL")

    settings.SECURE_PROXY_SSL_HEADER = tuple(env("SECURE_PROXY_SSL_HEADER"))
    settings.SENTRY_DSN = env("SENTRY_DSN")

    if settings.SENTRY_DSN:
        import sentry_sdk

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            enable_tracing=True,
        )

    if settings.HEALTH_CHECK_URL:
        CELERY_BEAT_SCHEDULE["health_check_task"]["enabled"] = True

    settings.HEADLESS_ONLY = True

    settings.ACCOUNT_RATE_LIMITS = {"login_failed": False}

    settings.AWS_CLOUDFRONT_DOMAIN = env("AWS_CLOUDFRONT_DOMAIN")

    settings_result = {"env": env}

    return settings_result
