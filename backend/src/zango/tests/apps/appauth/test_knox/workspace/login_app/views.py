from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView

from rest_framework.views import APIView

class TestDynamicView(APIView):
    def get(self, request, *args, **kwargs):
        return JsonResponse({"data": "data"}, status=200)
    
class TestDummyView(TemplateView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("<h1>Hey! This is dummy response from app.</h1>")
