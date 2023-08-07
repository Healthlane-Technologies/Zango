import sys
import types

from django.shortcuts import render
from django.views.generic import View
from django.http import Http404

from importlib import import_module
import threading

import sys
import importlib.machinery
import os

from .workspace.base import Workspace
meta_path_lock = threading.Lock()

class BlockingLoader(importlib.machinery.SourceFileLoader):
    pass

class BlockingFinder:
    BLOCKED_PATHS = ['/path/to/block', '/another/path/to/block']

    @classmethod
    def find_spec(cls, fullname, path, target=None):
        if path is None or path == "":
            path = sys.path
        for entry in path:
            if entry in cls.BLOCKED_PATHS:
                print(f"Blocking import from: {entry}")
                continue
            location = os.path.join(entry, fullname)
            loader = BlockingLoader(fullname, location)
            return importlib.machinery.ModuleSpec(fullname, loader, origin=location)



from contextlib import contextmanager
from django.conf import settings

@contextmanager
def tenant_sys_path(workspace):
    """
        Ensures that sys.path does not contain any other tenant's paths
        Adds the path of the workspace and its plugins to sys.path
    """
    original_sys_path = sys.path[:]
    temp_sys_path = []
    for o in original_sys_path:
        if "workspaces" not in o:
            temp_sys_path.append(o)
        temp_sys_path.append(str(settings.BASE_DIR)+f"/workspaces/{workspace}/plugins")
        # print(sys.path)
        temp_sys_path.append(str(settings.BASE_DIR)+f"/workspaces/{workspace}")
    try:
        sys.path = temp_sys_path
        yield
    finally:
        sys.path = original_sys_path


import importlib.util
import time

def import_with_timestamp(module_name):
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        raise ModuleNotFoundError(f"No module named '{module_name}'")
    
    module = importlib.util.module_from_spec(spec)
    module.__dict__['loaded_time'] = time.ctime()  # Add the timestamp here.
    spec.loader.exec_module(module)
    
    return module



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

    def dispatch(self, request, *args, **kwargs):
        # And here
        # with meta_path_lock:
        #     sys.meta_path.insert(0, BlockingFinder)

        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):        
         with tenant_sys_path(request.tenant.name):
            ws = Workspace(request.tenant, request)
            view =  ws.match_view(request)            
            if view:
                return view(request, *args, **kwargs)
            else:
                raise Http404()
            
                
    def post(self, request, *args, **kwargs):
         with tenant_sys_path(request.tenant.name):
            ws = Workspace(request.tenant, request)
            view =  ws.match_view(request)            
            if view:
                return view(request, *args, **kwargs)
            else:
                raise Http404()

    
    def put(self, request, *args, **kwargs):
        return
    
    def delete(self, request, *args, **kwargs):
        return

    



