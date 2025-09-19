import json

from allauth.headless.account.views import SessionView

from zango.core.api import get_api_response

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name='dispatch')
class AppLogoutViewAPIV1(SessionView):
    def get(self, request, *args, **kwargs):
        resp = super().get(request, *args, **kwargs)
        resp_data = json.loads(resp.content.decode("utf-8"))
        return get_api_response(
            success=True,
            response_content=resp_data,
            status=resp.status_code,
        )
