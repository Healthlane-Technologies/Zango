
import sys

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition



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
    # 'nocaptcha_recaptcha',
    'zelthy.apps.shared.tenancy',
    'zelthy.apps.shared.platformauth',
     
]


TENANT_APPS = [
    # The following Django contrib apps must be in TENANT_APPS
    'django.contrib.contenttypes',
    'zelthy.apps.appauth',
    'zelthy.apps.permissions',
    'zelthy.apps.dynamic_models',
    'corsheaders',
    "debug_toolbar",
    'crispy_forms',
    "crispy_bootstrap4",
    # "cachalot",

]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

TENANT_MODEL = "tenancy.TenantModel"
TENANT_DOMAIN_MODEL = "tenancy.Domain"



MIDDLEWARE = [
    'zelthy.middleware.tenant.ZelthyTenantMainMiddleware',    
    # 'zelthy.middleware.context_middleware.SimpleContextMiddleware',
    # 'zelthy.middleware.tenant_url_switch.url_switch_middleware',        
    # 'django_tenants.middleware.main.TenantMainMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',    
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'zelthy.middleware.request.RequestMiddleware',
    # 'zelthy.middleware.middleware.SetUserRoleMiddleWare',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'corsheaders.middleware.CorsMiddleware',
     "debug_toolbar.middleware.DebugToolbarMiddleware",
]


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
                'zelthy.template_loader.AppTemplateLoader',
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',                                             
            ]
        },
    },
]



DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

MIGRATION_MODULES = {}
RUNNING_ZMAKEMIGRATIONS = False

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    
    # ...
]

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',  # Using DB 1 for cache
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': 300,  # Default timeout is 5 minutes, but adjust as needed
    }
}

# DEBUG_TOOLBAR_PANELS += ['cachalot.panels.CachalotPanel',]

CACHALOT_ENABLED = False

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"

CRISPY_TEMPLATE_PACK = 'bootstrap4'
