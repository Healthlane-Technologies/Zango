import requests

from django.conf import settings


class TenantMixin:
    def get_tenant(self, **kwargs):
        from zango.apps.shared.tenancy.models import TenantModel

        obj = TenantModel.objects.get(uuid=kwargs.get("app_uuid"))
        return obj


class CaptchaMixin:
    def verify_captcha(self, request, *args, **kwargs):
        r = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": settings.RECAPTCHA_SECRET_KEY,
                "response": request.data["g-recaptcha-response"],
            },
        )

        if r.json()["success"]:
            return True, "Success"
        return False, r.json()["error-codes"]
