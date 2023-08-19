from .models import AggAuthor
from .models import AggBook
import random
from django.http import HttpResponse, JsonResponse
from django.views import View


class View1(View):

    def get(self,request,id, *args, **kwargs):
        a = AggAuthor.objects.create(name=f"{request.tenant.schema_name}_author_{id}")
        b = AggBook.objects.create(title=f"book_title_{id}", author=a, price=random.randint(10, 100000))

        return JsonResponse({})