from django.contrib import admin

# Register your models here.
from .models import PlatformUserModel

admin.site.register(PlatformUserModel)