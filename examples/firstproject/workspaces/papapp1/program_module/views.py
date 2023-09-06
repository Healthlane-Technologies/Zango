from django.views import View
from django.http import JsonResponse, HttpResponse
from django.views.generic import TemplateView
from django.shortcuts import render

from rest_framework import status
from rest_framework.response import Response # Not woring with View
from rest_framework.views import APIView # Not woring properly : for get kwargs is {}

from .models import ProgramModel
from . serializers import ProgramModelSerializer
from .forms import ProgramForm


class ProgramView(View):
    def get(self, request, *args, **kwargs):
        _id = request.GET.get('id')
        if _id:
            try:
                cmp_acc_obj = ProgramModel.objects.get(id=_id)
                serializer = ProgramModelSerializer(cmp_acc_obj)
                context = {"success": True, "data": serializer.data}
                return JsonResponse(context, status=status.HTTP_200_OK)
            except:
                context = {"success": False, "msg": "Please give valid program id."}
                return JsonResponse(context, status=status.HTTP_404_NOT_FOUND)
            
        context = {"success": False, "msg": "Please give program id."}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request, *args, **kwargs):
        serializer = ProgramModelSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            context = {"success": True, "msg": "Program addedd successfully..!", "data": serializer.data}
            return JsonResponse(context, status=status.HTTP_201_CREATED)
        else:
            context = {"success": False, "msg": "Program addedd failed..!", "error": serializer.errors}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)
    



# class ProgramFormView(View):
#     template_name = 'program_form.html'
    
#     def post(self, request):
#         form = ProgramForm(request.POST)
#         if form.is_valid():
#             form.save()
#             context = {"msg": "Data saved..!"}
#         else:
#             context = {"msg": "Data NOT saved..!"}
#         return HttpResponse(context)
    

#     def get(self, request):
#         form = ProgramForm()
#         context = {"form": form}
#         return context


class ProgramFormView(View):
    template_name = 'program_form.html'

    def get(self, request, *args, **kwargs):
        form = ProgramForm()
        context = {"form": form}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        print("kwargs ---------==> ", kwargs)
        form = ProgramForm(request.POST)
        if form.is_valid():
            form.save()
            context = {"msg": "Data saved..!"}
        else:
            context = {"msg": "Data NOT saved..!"}
        context["form"] = ProgramForm()
        return render(request, self.template_name, context)