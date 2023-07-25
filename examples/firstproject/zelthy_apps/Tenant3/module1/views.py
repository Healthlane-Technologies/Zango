from django.http import JsonResponse
from django.views.generic import TemplateView

from .helpers import x
from .helpers import y
from .helpers import z



def view1(request, *args, **kwargs):
    response = {"msg": "hello world"}    
    return JsonResponse(response)


# from condense-frame.frame.views.base import CondenseFrameBase
from .models import MyUser
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





class View2(TemplateView):

    template_name = 'hello_world.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        new_user = MyUser(name="John Doe", email=generate_random_email(), city="San Francisco" )
        session.add(new_user)
        session.commit()
        context['users'] = session.query(MyUser).all()

        return context

