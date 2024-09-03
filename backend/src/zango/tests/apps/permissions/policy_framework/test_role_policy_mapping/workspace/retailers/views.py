from django.http import HttpResponse
from zango.apps.dynamic_models.views import DynamicView


class DynamicRetailerView(DynamicView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("<h1>Hello World</h1>")

class DummyTestView(DynamicView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("<h1>This is a dummy get view.</h1>")
