import sys
import types

from django.shortcuts import render
from django.views.generic import View
from importlib import import_module


# Create your views here.
class DynamicView(View):
    """
        this class is responsible for building the 
    
    
    """
    tenant = None


    def get_tenant_settings(self):
        pass

    def get_tenant_urls(self):
        """
            builds the url patterns from the Apps' settings.py 
        """
        pass

    def match_route(self, path):
        """
            matches the path to the url patterns
        """
        pass

    def get_view_module(self):
        """
            set sys.path to the module path                            
            dynamically import view module and get view class
        """
        pass

    def get(self, request, *args, **kwargs):
        print(any("zelthy_apps" in m for m in sys.modules.keys()))
        from django.conf import settings
        module_name = str(settings.BASE_DIR) +'/zelthy_apps/Tenant3/zelthy_packages'
        sys.path.append(module_name)
        print(sys.path)
        # my_dynamic_module = types.ModuleType(module_name)
        # sys.modules[module_name] = my_dynamic_module 
        view = getattr(import_module("zelthy_apps.Tenant3.module1.views"), "View2")  
        print(any("zelthy_apps" in m for m in sys.modules.keys()))
        return view.as_view()(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return
    
    def put(self, request, *args, **kwargs):
        return
    
    def delete(self, request, *args, **kwargs):
        return

    



