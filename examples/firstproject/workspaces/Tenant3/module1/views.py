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


from .models import Item, Property, PropertyValue
from ..landingPage.models import LandingPageModel

@method_decorator(csrf_exempt, name='dispatch')
class View2(TemplateView):

    template_name = 'hello_world.html'

    def get_context_data(self, **kwargs):        
        context = super().get_context_data(**kwargs)
        val = PropertyValue.objects.create(label="testProp1")        
        item = Item.objects.create(title='MyItem')
        pg = LandingPageModel.objects.create(page="123")
        p = Property.objects.create(item=item, key="123", value=val, pg=pg)
        # p.odelete()
        # objs = Property.objects.all().values('item_id')
        prop = Property.objects.filter(id__lte=3230)    
        # print(prop)    
        pp = Property.objects.all()
        # print("all", pp)
        # print(Property.objects.get(id=329))
        print(Property.objects.all())
        print(Property.objects.none())
        # Property.objects.get(id=329).delete()

        # print(Property.objects.annotate(new_id=F('id') + 10000).values('new_id'))
        return context  
    
    def post(self, request, *args, **kwargs):
        return JsonResponse({'msg': 'post_response'})
    
