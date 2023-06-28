from django.views import View
from django.http import HttpResponse
from .test_zfrom import x
from ..abc import z
from zel-email.module1.views.pages.email_tableview import ZelthyCustomView, y
from communication.view import xx

class ZelthyCustomView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("Hello, world!%d %s"%(int(y), xx))