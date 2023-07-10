
from typing import Any, Dict
from django.views.generic import TemplateView
from django.http import JsonResponse
from .models import Patient


class AppLandingPageView(TemplateView):

    template_name = 'applandingPage.html'
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        patients = Patient.objects.all()
        return super().get_context_data(**kwargs)


def app_landing(request, *args, **kwargs):
    return JsonResponse({"msg": "Hello"})


    