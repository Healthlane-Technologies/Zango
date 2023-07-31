from django.http import JsonResponse
from django.views.generic import TemplateView

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
from .models import TestModel1
# from .models import FrameModel
from .models import FrameModel, FrameModel
from zelthy3.backend.apps.tenants.appauth.models import UserRoleModel
# from .models_1 import Patient
# from .models_1 import Doctor
# from frame.frame.models import Prescription
# from frame.configure.models import Instance
from datetime import datetime
class View2(TemplateView):

    template_name = 'hello_world.html'

    def get_context_data(self, **kwargs):        
        context = super().get_context_data(**kwargs)
        test = TestModel1(name='test').save()
        role = UserRoleModel.objects.get(id=1)
        from datetime import date
        
        frame = FrameModel(role=role, config={'a':1}, timestamp=date.today()).save()
        # print(test)
        print("Frames---->>", FrameModel.objects.filter(role=role))
        frame1 = FrameModel.objects.get(id=28)
        frame1.many_test.add(role)
        role2 = UserRoleModel.objects.get(id=2)
        frame1.many_test.add(role2)
        print(context)
        
        return context  
        # doctor = Doctor(
        #         name="John Doe", 
        #         specialization="gastroenterologist", 
        #         phone="+917738011774",
        #         email=generate_random_email()
        #         )                        
               
        # # session.commit()        
        # # print(new_user.id)
        # patient = Patient(
        #     name=2,#"Test Patient",
        #     age=23,
        #     phone="+817748011774",
        #     # gender='male',
        #     email=generate_random_email(),
        #     address="XYZ Street 123",            
        # )
        # patient.doctor = doctor
        # session.add(doctor) 
        # session.add(patient)
        
        # rx = Prescription(
        #     medicine_name='Janumet',
        #     quantity=2,
        #     instructions="Take 2 pills",
        #     date_prescribed=datetime.now()
        # )
        # rx.patients = patient
        # rx.doctors = doctor
        # session.add(rx)
        # session.commit()
        # # address = Address(address="123 Main St", user_id=new_user.id)
        # # session.add(address)
        # # address = Address(address="123 Main St", user_id=new_user.id)
        # # session.add(address)
        # # session.commit()
        # qr_patient = session.query(Patient).get(13)
        # qr_patient_ass = session.query(Patient).get(12)
        # qr_patient_ass1 = session.query(Patient).get(14)
        # print(qr_patient.prescriptions)
        # for rx in qr_patient.prescriptions:
        #     print(rx.id, rx.medicine_name)
        # # context['users'] = session.query(MyUser).all()
        # # context['new_user'] = new_user
        # # context['addresses'] = new_user.addresses
        # new_instance1 = Instance(number=1001, date=datetime.now())
        # new_instance2 = Instance(number=1002, date=datetime.now())
        # qr_patient.instances.append(new_instance1)
        # qr_patient.instances.append(new_instance2)
        # qr_patient.associated_patients.append(qr_patient_ass)
        # qr_patient.associated_patients.append(qr_patient_ass1)
        # session.commit()
        # print(qr_patient.instances)
        # for i in qr_patient.instances:
        #     print(i.id)
        # print(qr_patient.associated_patients)
        # return context

