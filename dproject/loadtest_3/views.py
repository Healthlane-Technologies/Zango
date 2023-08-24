from .models import AggAuthor
from .models import AggBook
from .models import ModelA
from .models import ModelB
from .models import ModelC
import random
from django.http import HttpResponse, JsonResponse, HttpResponseServerError
from django.views import View
from uuid import uuid4
import csv

class View1(View):

    def get(self,request,id, *args, **kwargs):
        author_id = str(uuid4())
        data = [
            [author_id]
        ]
        
        a = AggAuthor.objects.create(name=f"{author_id}")
        b = AggBook.objects.create(title=f"book_title_{id}", author=a, price=random.randint(10, 100000))

        if a.name != author_id:
            return HttpResponseServerError("Error occured")
        with open("ids.csv", "a+") as f:
            writer = csv.writer(f)
            for row in data:
                writer.writerow(row)
        return JsonResponse({})

class View2(View):

    def get(self, request, *args, **kwargs):
        _ = random.randint(10, 10000)
        model_a_instance = ModelA(
            field_a1=f"FieldA1_{random.randint(1, 100)}",
            field_a2=random.randint(1, 100),
            field_a3=random.choice([True, False]),
            field_a4='2023-08-23',  # Replace with appropriate date format
            field_a5=random.uniform(0, 1000),
            field_a6=f"Random text {_}",
            field_a7=f"random{_}@example.com",
            field_a8=f"http://www.random{_}.com",
            field_a9=f"images/random{_}.jpg",
            field_a10=random.uniform(0, 100),
        )
        model_a_instance.save()

        # Create ModelB instance with random data
        model_b_instance = ModelB(
            field_b1=f"FieldB1_{random.randint(1, 100)}",
            field_b2=random.randint(1, 100),
            field_b3=random.choice([True, False]),
            field_b4='2023-08-23',  # Replace with appropriate date format
            field_b5=random.uniform(0, 1000),
            field_b6=f"Random text {_}",
            field_b7=f"random{_}@example.com",
            field_b8=f"http://www.random{_}.com",
            field_b9=f"images/random{_}.jpg",
            field_b10=random.uniform(0, 100),
            model_a=model_a_instance,  # Assign the ForeignKey
        )
        model_b_instance.save()

        # Create ModelC instance with random data
        model_c_instance = ModelC(
            field_c1=f"FieldC1_{random.randint(1, 100)}",
            field_c2=random.randint(1, 100),
            field_c3=random.choice([True, False]),
            field_c4='2023-08-23',  # Replace with appropriate date format
            field_c5=random.uniform(0, 1000),
            field_c6=f"Random text {_}",
            field_c7=f"random{_}@example.com",
            field_c8=f"http://www.random{_}.com",
            field_c9=f"images/random{_}.jpg",
            field_c10=random.uniform(0, 100),
            model_b=model_b_instance,  # Assign the OneToOneField
        )
        model_c_instance.save()
        return JsonResponse({})