import os
import json
import random
import subprocess
import django
import argparse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'firstproject.settings')
django.setup()

from zelthy.apps.shared.tenancy.models import TenantModel, Domain

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

def generate_models(path: str, module_num, no_of_models):
    with open(path, "a") as f:
        # Generate code for 20 models with the specified fields

        models_code = []
        for i in range(no_of_models+1):
            model_code = f"class Model{i}Mod{module_num}(DynamicModelBase):\n"
            for field in fields:
                model_code += f"    {field}\n"
            models_code.append(model_code)

        f.write("\n\n".join(models_code))

        f.write(f"class ModelAuthor{module_num}(DynamicModelBase):\n")
        f.write("    name = models.CharField(max_length=100)\n")

        f.write(f"class ModelBook{module_num}(DynamicModelBase):\n")
        f.write(f"    author = ZForeignKey(ModelAuthor{module_num}, on_delete=models.CASCADE)\n")

def create_tenant_folder(tenant):
    os.makedirs(f"workspaces/{tenant}")
    settings = {
        "version": "1.0.0",
        "modules": [],
        "app_routes": [],
        "plugin_routes": []
    }
    plugins = {
        "plugins": []
    }
    with open(f"workspaces/{tenant}/settings.json", "w") as f:
        json.dump(settings, f, indent=4)
    with open(f"workspaces/{tenant}/plugins.json", "w") as f:
        json.dump(plugins, f, indent=4)

def generate_modules(no_of_modules: int, tenant: str, no_of_models, no_of_models_in_view):
    for i in range(no_of_modules):
        if not os.path.exists(f"workspaces/{tenant}"):
            create_tenant_folder(tenant)
        os.makedirs(f"workspaces/{tenant}/mod{i}")
        
        with open(f"workspaces/{tenant}/mod{i}/models.py", "w") as f:
            f.writelines(["from django.db import models\n", "from zelthy.apps.dynamic_models.models import DynamicModelBase\n", "from zelthy.apps.dynamic_models.fields import ZForeignKey\n\n\n"])
        
        generate_models(f"workspaces/{tenant}/mod{i}/models.py", i, no_of_models)

        model_nums = generate_unique_random_numbers(no_of_models_in_view, 0, no_of_models)
        with open(f"workspaces/{tenant}/mod{i}/views.py", "w") as f:
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
        
        with open(f"workspaces/{tenant}/mod{i}/urls.py", "w") as f:
            f.write("from django.urls import re_path\n")
            f.write("from .views import View1\n\n")
            f.write("urlpatterns = [re_path(r'^view1/$', View1.as_view(), name='view1')]\n")

def update_settings(tenant_name, num:int):
    new_routes = []
    new_paths = []
    for i in range(num):
        route = {
            "re_path": f"^mod{i}/",
            "module": f"mod{i}",
            "url": "urls"
        }
        new_routes.append(route)
        path = {
            "name": f"mod{i}",
            "path": f"mod{i}"
        }
        new_paths.append(path)
    data = None
    with open(f"workspaces/{tenant_name}/settings.json", "r+") as f:
        data = json.load(f)
        data["app_routes"].extend(new_routes)
        data["modules"].extend(new_paths)

    with open(f"workspaces/{tenant_name}/settings.json", "w") as f:
        json.dump(data, f, indent=4)

def migration_operations(tenant: str):
    subprocess.run(f"python manage.py ws_makemigrate {tenant}", shell=True)
    subprocess.run(f"python manage.py ws_migrate {tenant}", shell=True)

def create_tenant_and_domain(tenant, index):
    ten = TenantModel.objects.create(name=tenant, schema_name=tenant, description="desc")
    domain = Domain.objects.create(tenant=ten, domain=f"app{index}.zelthy.com")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--nt", help="No of tenants", type=int)
    parser.add_argument("--nm", help="No of models in each module", type=int)
    parser.add_argument("--nmod", help="No of modules in each tenant", type=int)
    parser.add_argument("--nmv", help="No of model in each view", type=int)
    args = parser.parse_args()
    tenant_num = args.nt
    no_of_models = args.nm
    no_of_modules = args.nmod
    no_of_models_in_view = args.nmv
    if tenant_num is None:
        tenant_num = 1
    if no_of_models is None:
        no_of_models = 20
    if no_of_modules is None:
        no_of_modules = 100
    if no_of_models_in_view is None:
        no_of_models_in_view = 5
    tenants = [f"loadtest_{i}" for i in range(tenant_num)]
    subprocess.run("python manage.py migrate_schemas", shell=True)
    for index, tenant in enumerate(tenants):
        create_tenant_folder(tenant)
        generate_modules(no_of_modules, tenant, no_of_models, no_of_models_in_view)
        update_settings(tenant, no_of_modules)
        create_tenant_and_domain(tenant, index)
        migration_operations(tenant)
