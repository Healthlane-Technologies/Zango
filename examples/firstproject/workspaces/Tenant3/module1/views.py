from typing import Any
from django import http
from django.http import JsonResponse
from django.views.generic import TemplateView
from django.views.generic import View
from datetime import date
from django.apps import apps
from .helpers import x
from .helpers import y
from .helpers import z
from django.db.models import Q
from django.db.models import F


from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


from .models import Item, Property, PropertyValue, StateModel
from ..landingPage.models import LandingPageModel

@method_decorator(csrf_exempt, name='dispatch')
class View2(TemplateView):

    template_name = 'hello_world.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["objects"] = StateModel.objects.all().count()
        # context['objects'] = Property.objects.all().count()
        # StateModel.objects.create(name='Karn')
        # print(StateModel.objects.all())
        # obj = StateModel.objects.get(id=13)
        # obj.name = "Karn1"
        # obj.save()
        return context  
    
    def post(self, request, *args, **kwargs):
        return JsonResponse({'msg': 'post_response'})
    
