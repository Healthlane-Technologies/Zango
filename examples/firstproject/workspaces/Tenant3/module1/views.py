from django.http import JsonResponse
from django.views.generic import TemplateView
from datetime import date
from django.apps import apps
from .helpers import x
from .helpers import y
from .helpers import z
from django.db.models import Q


from .models import Item, Property, PropertyValue
from ..landingPage.models import LandingPageModel

class View2(TemplateView):

    template_name = 'hello_world.html'

    def get_context_data(self, **kwargs):        
        context = super().get_context_data(**kwargs)
        # print("Property", PropertyValue)
        val = PropertyValue.objects.create(label="testProp1")        
        item = Item.objects.create(title='MyItem')
        
        
        # ite = Item.objects.get(id=2)
        pg = LandingPageModel.objects.create(page="123")
        p = Property.objects.create(item=item, key="123", value=val, pg=pg)

        # p.values.add(val)
        # p.save()
        # print(p.values.all())
        # print("pp--->", p.values.all())
        # print(ite.props.all()[0].item.title)
        # print(p)
        # pg1 = LandingPageModel.objects.get(id=1)
        # print(pg1.property_set.all())
        return context  
        
