from threading import local

from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

_request_local = local()

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _request_local.current_request = request
        from django.apps import apps
        model = apps.get_model('appauth', 'UserRoleModel')
        obj_store_model = apps.get_model('object_store', 'ObjectStore')
        try:
            _request_local.user_role = model.objects.get(id=request.session['role_id'])
        except:
            if request.tenant.tenant_type == 'app':  
                _request_local.user_role = model.objects.get(name='AnonymousUsers')
            else:
                _request_local.user_role = None # user role is not applicable at platform level

        try:
            user = request.user
            if _request_local.user_role:
                _request_local.app_object = user.get_app_object(_request_local.user_role.id)
            else:
                _request_local.app_object = None
        except Exception as e:
            print(str(e))
            _request_local.app_object = None
        response = self.get_response(request)
        return response


class HomePageMiddleware(MiddlewareMixin):
    """
    Middleware class for redirecting the root path to the home page.

    This middleware checks if the requested path is the root path ("/") and if the user is authenticated. 
    If both conditions are met, it redirects the user to the home page ("/app/home").

    Attributes:
        None

    Methods:
        process_request(request): Checks if the requested path is the root path and if the user is authenticated. 
        If both conditions are met, it redirects the user to the home page.
    """
    def process_request(self, request):

        is_root_path = request.path == '/'
        if is_root_path:
            if not request.user.is_anonymous and not request.user.__class__.__name__ == "PlatformUserModel":
                return redirect('/app/home')
            