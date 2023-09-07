from threading import local

_request_local = local()

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _request_local.current_request = request
        try:
            # _request_local.user_role = request.session['role_id'] #TODO
            from django.apps import apps
            model = apps.get_model('appauth', 'UserRoleModel')
            _request_local.user_role = model.objects.get(id=request.session['role_id'])

        except:
            _request_local.user_role = None
        
        response = self.get_response(request)
        return response
