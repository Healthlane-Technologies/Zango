import os
import json
import random
import os
import django
import subprocess

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dproject.settings')
django.setup()

from tenancy.models import TenantModel, Domain

num_numbers = 5
start_range = 0
end_range = 20

def generate_unique_random_numbers(num_numbers, start_range, end_range):
    if num_numbers > (end_range - start_range + 1):
        raise ValueError("Cannot generate more unique numbers than the available range.")

    unique_numbers = set()
    while len(unique_numbers) < num_numbers:
        num = random.randint(start_range, end_range)
        unique_numbers.add(num)

    return list(unique_numbers)


fields = [
    "field1 = models.CharField(max_length=100)",
    "field2 = models.IntegerField()",
    "field3 = models.BooleanField(default=False)",
    "field4 = models.IntegerField(default=10)",
    "field5 = models.DateField(auto_now_add=True)",
    "field6 = models.CharField(max_length=254, default='field')",
    "field7 = models.CharField(max_length=200, default='field')",
    "field8 = models.TextField(default='def')",
    # Add more field definitions here
]

def generate_models(path: str, module_num):
    with open(path, "a") as f:
        # Generate code for 20 models with the specified fields
        num_models = 20

        models_code = []
        for i in range(num_models+1):
            model_code = f"class Model{i}Mod{module_num}(models.Model):\n"
            for field in fields:
                model_code += f"    {field}\n"
            models_code.append(model_code)

        f.write("\n\n".join(models_code))

        f.write(f"class ModelAuthor{module_num}(models.Model):\n")
        f.write("    name = models.CharField(max_length=100)\n")

        f.write(f"class ModelBook{module_num}(models.Model):\n")
        f.write(f"    author = models.ForeignKey(ModelAuthor{module_num}, on_delete=models.CASCADE)\n")

def generate_modules(num: int, tenant: str):
    for i in range(2, num+2):
        with open(f"{tenant}/models.py", "w") as f:
            f.writelines(["from django.db import models\n", ])
        
        generate_models(f"{tenant}/models.py", i)

        model_nums = generate_unique_random_numbers(num_numbers, start_range, end_range)
        with open(f"{tenant}/views.py", "w") as f:
            f.write("from django.views import View\n")
            f.write("from django.http import JsonResponse\n")
            for model_num in model_nums:
                f.write(f"from .models import Model{model_num}Mod{i}\n")
            f.write(f"from .models import ModelAuthor{i}\n")
            f.write(f"from .models import ModelBook{i}\n")

            f.write("\n\n")
            f.write("class View1(View):\n")
            f.write("    def get(self, request, *args, **kwargs):\n")
            for model_num in model_nums:
                f.write(f"        mod = Model{model_num}Mod{i}.objects.create(field1='dota', field2=2)\n")
            f.write(f"        mod = ModelAuthor{i}.objects.create(name='a')\n")
            f.write(f"        bok= ModelBook{i}.objects.create(author=mod)\n")
            f.write("        return JsonResponse({})")
        
        with open(f"{tenant}/urls.py", "w") as f:
            f.write("from django.urls import re_path\n")
            f.write("from .views import View1\n\n")
            f.write("urlpatterns = [re_path(r'^view1/$', View1.as_view(), name='view1')]\n")

def append_tenant_apps(tenants):
    tenants = f"({','.join(tenants)})"
    with open("dproject.settings.py", "a") as f:
        f.write(f"TENANT_APPS += {tenants}\n")
        f.write("INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]\n")

def append_urls(tenants):
    with open(f"dproject/url_tenants.py", "w") as f:
        f.write("from django.urls import path, include\n\n")
        f.write("urlpatterns = [\n")
        for tenant in tenants:
            f.write(f"    re_path('mod1/', include('{tenant}.urls')),\n")
        f.write("]\n")

def migration_operations(tenants):
    subprocess.run("python manage.py migrate_schemas", shell=True)
    for tenant in tenants:
        subprocess.run(f"python manage.py tenant_command migrate --schema {tenant}")

def create_tenants_and_domains(tenants):
    for index, tenant in enumerate(tenants):
        ten = TenantModel.objects.create(name=tenant, schema_name=tenant, description="desc")
        domain = Domain.objects.create(tenant=ten, domain=f"app{index}.zelthy.com")

if __name__ == "__main__":
    tenant_num = 1
    model_num = 100
    tenants = [f"loadtest_{i}" for i in range(tenant_num)]
    for tenant in tenants:
        generate_modules(model_num, tenant)
    append_tenant_apps(tenants)
    append_urls(tenants)
    create_tenants_and_domains(tenants)
