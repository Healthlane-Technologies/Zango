
from django.http import HttpResponse
from django.views import View
from django.views.generic import TemplateView


class ZelthyCustomView(TemplateView):

    template_name = "hello_world.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = "Hello, World!"
        context['name'] = kwargs.get('code')
        context['ip_address'] = self.get_ip_address()
        return context

    def get_ip_address(self):
        # Get IP address of the user
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = self.request.META.get('REMOTE_ADDR')
        return ip_address





