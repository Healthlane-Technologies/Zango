from django.contrib import admin

# Register your models here.
from .models import *

admin.site.register(TenantModel)
admin.site.register(Domain)
admin.site.register(ThemesModel)
