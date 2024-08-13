from django.http import HttpResponse
from django.views.generic import TemplateView


class TestDynamicView(TemplateView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("<h1>Hello World</h1>")
