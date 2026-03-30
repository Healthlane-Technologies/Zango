import json
import requests

from django.conf import settings


class TenantMixin:
    def get_tenant(self, **kwargs):
        from zango.apps.shared.tenancy.models import TenantModel

        obj = TenantModel.objects.get(uuid=kwargs.get("app_uuid"))
        return obj


class CaptchaMixin:
    def verify_captcha(self, request, *args, **kwargs):
        # Support both DRF Request (.data) and plain Django HttpRequest.
        recaptcha_response = None
        if hasattr(request, "data"):
            recaptcha_response = request.data.get("g-recaptcha-response")
        if not recaptcha_response:
            recaptcha_response = request.POST.get("g-recaptcha-response")
        if not recaptcha_response and request.body:
            try:
                recaptcha_response = json.loads(request.body).get(
                    "g-recaptcha-response"
                )
            except Exception:
                recaptcha_response = None

        r = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": settings.RECAPTCHA_PRIVATE_KEY,
                "response": recaptcha_response,
            },
        )

        if r.json()["success"]:
            return True, "Success"
        return False, r.json()["error-codes"]
