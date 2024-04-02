from django.contrib import admin

# Register your models here.
from .models import TenantModel, Domain, ThemesModel

admin.site.register(TenantModel)
admin.site.register(Domain)
admin.site.register(ThemesModel)
