from threading import local

_request_local = local()

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _request_local.current_request = request
        from django.apps import apps
        model = apps.get_model('appauth', 'UserRoleModel')
        try:
            _request_local.user_role = model.objects.get(id=request.session['role_id'])
        except:
            if request.tenant.tenant_type == 'app':  
                _request_local.user_role = model.objects.get(name='AnonymousUsers')
            else:
                _request_local.user_role = None # user role is not applicable at platform level
        response = self.get_response(request)
        return response
