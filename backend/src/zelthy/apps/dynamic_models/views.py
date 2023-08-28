import sys
import types
import time
from django.shortcuts import render
from django.views.generic import View
from django.http import Http404

from importlib import import_module
import threading

import sys
import importlib.machinery
import os
import threading

lock = threading.Lock()

from .workspace.base import Workspace

meta_path_lock = threading.Lock()


class BlockingLoader(importlib.machinery.SourceFileLoader):
    pass


class BlockingFinder:
    BLOCKED_PATHS = ["/path/to/block", "/another/path/to/block"]

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
        temp_sys_path.append(
            str(settings.BASE_DIR) + f"/workspaces/{workspace}/plugins"
        )
        # print(sys.path)
        temp_sys_path.append(str(settings.BASE_DIR) + f"/workspaces/{workspace}")
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
    module.__dict__["loaded_time"] = time.ctime()  # Add the timestamp here.
    spec.loader.exec_module(module)

    return module


def reset_modules():
    modules_to_delete = []
    for module_name, module in sys.modules.items():
        try:
            if "workspaces" in module.__file__:
                modules_to_delete.append(module_name)
        except:
            # print(type(m))
            pass
    for module in modules_to_delete:
        del sys.modules[module]


# Create your views here.
class DynamicView(View):
    """
    this class is responsible for building the


    """

    tenant = None
    _lock = threading.Lock()
    path = []
    modules = None

    def get(self, request, *args, **kwargs):
        # with self._lock:
        #     if not self.path:
        #         self.path = sys.path[:]
        #     else:
        #         sys.path = self.path
        #     if not self.modules:
        #         self.modules = sys.modules.copy()
        #     else:
        #         sys.modules = self.modules.copy()
        # print("Lock acquired: ", threading.current_thread())
        #     # time.sleep(5)
        # reset_modules()
        # with tenant_sys_path(request.tenant.name):
        ws = Workspace(request.tenant, request)
        ws.ready()
        view = ws.match_view(request)
        if view:
            resp = view(request, *args, **kwargs)
            return resp
        raise Http404()

    def post(self, request, *args, **kwargs):
        with tenant_sys_path(request.tenant.name):
            ws = Workspace(request.tenant, request)
            view = ws.match_view(request)
            if view:
                return view(request, *args, **kwargs)
            else:
                raise Http404()

    def put(self, request, *args, **kwargs):
        return

    def delete(self, request, *args, **kwargs):
        return
