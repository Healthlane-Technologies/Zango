def get_current_request():
    from ..middleware.request import _request_local

    return getattr(_request_local, "current_request", None)


def get_current_role():
    from ..middleware.request import _request_local
    from django.apps import apps

    # model = apps.get_model('appauth', 'UserRoleModel')
    return getattr(_request_local, "user_role", None)
    # return model.objects.get(id=user_role_id)


def get_package_url(tenant, package_name, path):
    """
    returns the root path of the package
    """
    ws_klass = getattr(
        import_module("zelthy.apps.dynamic_models.workspace.base"), "Workspace"
    )
    ws = ws_klass(tenant)
    ws_settings = ws.get_workspace_settings()
    plugin_root_path = ws_settings["plugin_routes"][package_name]
    return f"http://{domain_url}/{plugin_root_path}/{path}"  # this is used for internal routing so http should suffice


def get_current_request_url(request, domain=None):
    # Determine the protocol (HTTP or HTTPS) based on the request's is_secure() method.
    protocol = "https" if request.is_secure() else "http"

    # Get the hostname (domain) from the request.
    if not domain:
        domain = request.get_host()

    # Get the port from the request. Use the standard ports (80 for HTTP, 443 for HTTPS) as default.
    port = request.META.get("SERVER_PORT", "")
    if (protocol == "http" and port == "80") or (protocol == "https" and port == "443"):
        port_string = ""
    else:
        port_string = f":{port}"

    # Construct and return the complete URL.
    current_url = f"{protocol}://{domain}{port_string}"
    return current_url
