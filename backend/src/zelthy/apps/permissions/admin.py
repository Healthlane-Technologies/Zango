from django.contrib import admin
from zelthy.utils.pretty_json import JsonAdmin
# Register your models here.
from .models import PermissionsModel, PolicyModel, PolicyGroupModel


admin.site.register(PermissionsModel)
admin.site.register(PolicyModel, JsonAdmin)
admin.site.register(PolicyGroupModel)