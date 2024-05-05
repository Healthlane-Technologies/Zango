
import sys
from contextlib import contextmanager
from django.conf import settings


@contextmanager
def workspace_sys_paths(wname: str) -> list[str]:
    """
        Ensures that sys.path does not contain any other tenant's paths
        Adds the path of the workspace and its packages to sys.path
    """
    original_sys_path = sys.path[:]
    temp_sys_path = []
    for o in original_sys_path:
        if "zelthy_apps" not in o:
            temp_sys_path.append(o)
    temp_sys_path.append(str(settings.BASE_DIR)+ f"/workspaces/{wname}")
    temp_sys_path.append(str(settings.BASE_DIR)+ f"/workspaces/{wname}/zelthy_packages")

    try:
        sys.path = temp_sys_path
        yield
    finally:
        sys.path = original_sys_path