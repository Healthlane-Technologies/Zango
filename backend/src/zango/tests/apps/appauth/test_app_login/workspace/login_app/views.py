from django.http import HttpResponse
from django.views.generic import TemplateView

class TestDynamicView(TemplateView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("<h1>Hey! This is response from app after login.</h1>")
    
class TestDummyView(TemplateView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("<h1>Hey! This is dummy response from app.</h1>")
