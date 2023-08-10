
import sys
print(any("zelthy_apps" in m for m in sys.modules.keys()))

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition



SHARED_APPS = [
    'django_tenants',  # mandatory
    'zelthy3',
    
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
    'zelthy3.backend.apps.shared.apps',
    'zelthy3.backend.apps.shared.platformauth',
     
]


TENANT_APPS = [
    # The following Django contrib apps must be in TENANT_APPS
    'django.contrib.contenttypes',
    'zelthy3.backend.apps.tenants.appauth',
    'zelthy3.backend.apps.tenants.permissions',
    'zelthy3.backend.apps.tenants.dynamic_models',
    'corsheaders',

]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

TENANT_MODEL = "apps.AppModel"
TENANT_DOMAIN_MODEL = "apps.Domain"



MIDDLEWARE = [
    'zelthy3.middleware.ZelthyTenantMainMiddleware',    
    # 'django_tenants.middleware.main.TenantMainMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',    
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'zelthy3.middleware.SetUserRoleMiddleWare',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    # 'zelthy3.middleware.ClearModulesMiddleware'
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
                'zelthy3.template_loader.AppTemplateLoader',
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