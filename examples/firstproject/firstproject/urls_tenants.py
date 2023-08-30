from django.contrib import admin
from django.urls import path, include
print("here")
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('zelthy.config.urls_tenants')),
]

print(urlpatterns)