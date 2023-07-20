from django.http import JsonResponse
from django.views.generic import TemplateView
from zelthy3.backend.apps.tenants.datamodel.models import DynamicTable
from .models import TenantRole
from .models import TenantUser

from .helpers import x
from .helpers import y
from .helpers import z



def view1(request, *args, **kwargs):
    response = {"msg": "hello world"}    
    return JsonResponse(response)



class View2(TemplateView):

    template_name = 'hello_world.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)       
        context.update(**kwargs)
        context.update(x=x)
        context.update(y=y)
        context.update(z=z)        
        return context

def new_view(request, *args, **kwargs):
    a = TenantUser(name="zelthy")
    a.save()
    response = {"content": TenantUser.objects.first().name}
    return JsonResponse(response)

def foreign_view(request, *args, **kwargs):
    ref = TenantUser.objects.first()
    inst = TenantRole(usr=ref,admin=ref,role="test")
    inst.save()
    return JsonResponse({ "user": TenantRole.__module__ })