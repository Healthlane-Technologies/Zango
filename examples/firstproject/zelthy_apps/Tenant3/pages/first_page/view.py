
from django.http import HttpResponse
from django.views import View
from django.views.generic import TemplateView


class ZelthyCustomView(TemplateView):

    template_name = "hello_world.html"

    def get_context_data(self, **kwargs):
        context = super(ZelthyCustomView, self).get_context_data(**kwargs)
        context['message'] = "Hello, World!"
        return context

#    def get(self, request, *args, **kwargs):
#       return HttpResponse("Hello, World1114!")




