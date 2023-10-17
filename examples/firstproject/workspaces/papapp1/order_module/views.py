from django.views import View
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView
from django.shortcuts import render

from rest_framework import status
from rest_framework.response import Response # Not woring with View
from rest_framework.views import APIView # Not woring properly : for get kwargs is {}

from .models import OrderModel
from .serializers import OrderModelSerializer
from .forms import OrderForm





class OrderView(View):
    def get(self, request, *args, **kwargs):
        _id = request.GET.get('id')
        if _id:
            try:
                _obj = OrderModel.objects.get(id=_id)
                serializer = OrderModelSerializer(_obj)
                context = {"success": True, "data": serializer.data}
                return JsonResponse(context, status=status.HTTP_200_OK)
            except:
                context = {"success": False, "msg": "Please give valid order id."}
                return JsonResponse(context, status=status.HTTP_404_NOT_FOUND)
            
        context = {"success": False, "msg": "Please give order id."}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request, *args, **kwargs):
        serializer = OrderModelSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            context = {"success": True, "msg": "Order addedd successfully..!", "data": serializer.data}
            return JsonResponse(context, status=status.HTTP_201_CREATED)
        else:
            context = {"success": False, "msg": "Order addedd failed..!", "error": serializer.errors}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)
    




class OrderFormView(View):
    template_name = 'program_form.html'

    def get(self, request, *args, **kwargs):
        form = OrderForm()
        context = {"form": form}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        print("kwargs ---------==> ", kwargs)
        form = OrderForm(request.POST)
        if form.is_valid():
            form.save()
            context = {"msg": "Data saved..!"}
            context["form"] = OrderForm()
        else:
            print("form.errors ==> ", form.errors)
            context = {"msg": "Data NOT saved..!", "form": form}
        return render(request, self.template_name, context)