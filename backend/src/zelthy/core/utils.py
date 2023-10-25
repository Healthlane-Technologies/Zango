

def get_current_request():
    from ..middleware.request import _request_local
    return getattr(_request_local, 'current_request', None)

def get_current_role():
    from ..middleware.request import _request_local
    from django.apps import apps
    # model = apps.get_model('appauth', 'UserRoleModel')
    return getattr(_request_local, 'user_role', None)
    # return model.objects.get(id=user_role_id)
