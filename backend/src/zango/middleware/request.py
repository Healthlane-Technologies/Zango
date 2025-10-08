from threading import local

from rest_framework import exceptions

from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse


_request_local = local()


class UserRoleAndAppObjectAssignmentMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Processes the request to set the current request and user role within the request context.

        This method retrieves the UserRoleModel and ObjectStore models and attempts to set the user role based on the role_id stored in the request session.
        If no role is found, it defaults to the "AnonymousUsers" role for app tenants
        It also attempts to set the app_object based on the user's role, handling exceptions gracefully.
        """
        _request_local.current_request = request
        from django.apps import apps

        from zango.apps.appauth.auth_backend import KnoxTokenAuthBackend

        model = apps.get_model("appauth", "UserRoleModel")
        authTokenModel = apps.get_model("appauth", "AppUserAuthToken")
        obj_store_model = apps.get_model("object_store", "ObjectStore")
        try:
            _request_local.user_role = model.objects.get(id=request.session["role_id"])
        except Exception:
            if request.tenant.tenant_type == "app":
                if request.headers.get("Authorization"):
                    try:
                        resp = KnoxTokenAuthBackend().authenticate(request)
                        if resp:
                            user, token = resp
                            request.user = user
                            request.auth = token
                            apt = authTokenModel.objects.get(user=user)
                            _request_local.user_role = apt.role
                    except exceptions.AuthenticationFailed:
                        return JsonResponse({"message": "Unauthorized"}, status=401)
                    except Exception:
                        import traceback

                        traceback.print_exc()
                        _request_local.user_role = model.objects.get(
                            name="AnonymousUsers"
                        )
                else:
                    _request_local.user_role = model.objects.get(name="AnonymousUsers")
            else:
                _request_local.user_role = (
                    None  # user role is not applicable at platform level
                )

        try:
            user = request.user
            _request_local.user = request.user
            _request_local.META = request.META
            _request_local.headers = request.headers
            user_role = _request_local.user_role
            if (
                user_role
                and not user_role.name == "AnonymousUsers"
                and not isinstance(user, AnonymousUser)
            ):
                _request_local.app_object = user.get_app_object(
                    _request_local.user_role.id
                )
            else:
                _request_local.app_object = None
        except Exception as e:
            import traceback

            traceback.print_exc()
            _request_local.app_object = None
        response = self.get_response(request)
        return response
