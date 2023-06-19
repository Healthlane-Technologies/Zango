

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-)c3(unqe=siu7j&=ew+_o^fec9sujmik*mh4es)v^_&bpiy^b*'

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

]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

TENANT_MODEL = "apps.AppModel"
TENANT_DOMAIN_MODEL = "apps.Domain"



MIDDLEWARE = [
    'zelthy3.backend.middleware.ZelthyTenantMainMiddleware',
    # 'django_tenants.middleware.main.TenantMainMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
           
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',                
                'zelthy3.template_loader.AppTemplateLoader'
            ]
        },
    },
]



DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)


