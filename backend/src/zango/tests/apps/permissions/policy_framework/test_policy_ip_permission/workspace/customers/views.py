from django.http import HttpResponse
from django.views.generic import TemplateView


class TestDynamicView(TemplateView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("<h1>Hey! This is IP testing response</h1>")

class CIDRDynamicView(TemplateView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("<h1>Hey! This is CIDR IP testing response</h1>")
    
class AllIPDynamicView(TemplateView):
    def get(self, request, *args, **kwargs):
        return HttpResponse("<h1>Hey! This view can be viewed from all IPs.</h1>")
