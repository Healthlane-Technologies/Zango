from django.http import JsonResponse
from django.views.generic import TemplateView
from datetime import date
from django.apps import apps
from .helpers import x
from .helpers import y
from .helpers import z



def view1(request, *args, **kwargs):
    response = {"msg": "hello world"}    
    return JsonResponse(response)


# from condense-frame.frame.views.base import CondenseFrameBase


from zelthy3.sql_alchemy import engine
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()

import random
import string

def generate_random_email():
    # define the email domains and name lengths
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "aol.com"]
    min_name_length = 4
    max_name_length = 10

    # generate a random name
    name_length = random.randint(min_name_length, max_name_length)
    name = ''.join(random.choices(string.ascii_lowercase, k=name_length))

    # pick a random domain
    domain = random.choice(domains)

    return f"{name}@{domain}"


from sqlalchemy import insert

from zelthy3.backend.apps.tenants.permissions.models import PermissionsModel, PolicyModel
from zelthy3.backend.core.django_alchemy import DjangoModelConverter
permModel = DjangoModelConverter(PermissionsModel)
policyModel = DjangoModelConverter(PolicyModel)
# from .models import Address
# from .models import MyUser
# from .models import TestModel1
# from .models import FrameModel
# from .models import FrameModel, FrameModel
from zelthy3.backend.apps.tenants.appauth.models import UserRoleModel

# from .models_1 import Patient
# from .models_1 import Doctor
import sys
from frame.frame.views.configure import frameconfigureview

from landingPage.models import LandingPageModel

# from frame.configure.models import Instance
from datetime import datetime, date
from .models import Address
class View2(TemplateView):

    template_name = 'hello_world.html'

    def get_context_data(self, **kwargs):        
        context = super().get_context_data(**kwargs)
        # test = TestModel1(name='test').save()
        # role = UserRoleModel.objects.get(id=1)                
        # frame = FrameModel(role=role, config={'a':1}, timestamp=date.today()).save()
        # frame1 = FrameModel.objects.get(id=28)
        
        # print(FrameModel)
        # frame1.many_test.add(role)
        # role2 = UserRoleModel.objects.get(id=2)
        # frame1.many_test.add(role2)        
        # address = Address.objects.create(use='90849')
        # patient = Patient.objects.create(
        #         identifier="kdodi", name='Test', telecom='sodio', birthDate=date.today(), address=address)
        # # patient.address_1.add(address)
        # patient.save()
        print(Address)
        address1 = Address.objects.get(id=5)
        # print(address1.patient_set.all())
        print(address1.landingpagemodel_set.all())
        # print(patient.address.remote_field)
        context['landingpage'] = address1.landingpagemodel_set.all()
        return context  
        
