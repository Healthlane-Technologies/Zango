from django.contrib import admin

from .models import AppUserModel, UserRoleModel


admin.site.register(UserRoleModel)
admin.site.register(AppUserModel)
