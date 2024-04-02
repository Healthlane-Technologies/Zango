from django.contrib import admin
from .models import UserRoleModel, AppUserModel

admin.site.register(UserRoleModel)
admin.site.register(AppUserModel)
