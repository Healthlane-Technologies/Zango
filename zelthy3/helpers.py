
import json
from django.conf import settings

try:
    from django.apps import apps, AppConfig
    get_model = apps.get_model
except ImportError:
    from django.db.models.loading import get_model
    AppConfig = None

def get_app_base_dir(tenant):
    app_dir = settings.BASE_DIR / "zelthy_apps" / tenant.name
    return app_dir

def get_app_settings(tenant):
    app_dir =get_app_base_dir(tenant)
    settings_filepath = app_dir / "settings.json"
    with settings_filepath.open() as f:
        return json.load(f)
    

def get_module_path(tenant, module_name):
    app_settings = get_app_settings(tenant)
    modules = app_settings['modules']
    for mod in modules:
        if mod['name'] == module_name:
            return mod['path']
    packages = app_settings['packages']
    for pkg in packages:
        module_name.split("/")[0] == pkg["name"]
        return "zelthy_packages" + "/" + module_name
    return None

def get_mod_url_filepath(tenant, module_name):
    app_base_dir = get_app_base_dir(tenant)
    app_settings = get_app_settings(tenant)
    mod_path = get_module_path(tenant, module_name)
    routes = app_settings["routes"]
    for route in routes:
        if route["module"] == module_name:
            url = route["url"]
            url_filepath = app_base_dir / mod_path / url
            return url_filepath.with_suffix(".py")
    return None

def get_userrole_model():
    return get_model("appauth", "UserRoleModel")

def get_view_unique_name(module_name, callback):
    #TODO Handle for package
    if callback.__name__ == 'view':
        view_name = callback.view_class.__name__
    else:
        view_name = callback.__name__
    return module_name + "/" + view_name
    
    