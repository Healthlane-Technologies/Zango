from django.contrib import admin

# Register your models here.
from .models import PermissionsModel, PolicyGroupModel, PolicyModel


admin.site.register(PermissionsModel)
admin.site.register(PolicyModel)
admin.site.register(PolicyGroupModel)
