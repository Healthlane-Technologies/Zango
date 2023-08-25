from django.views import View
from django.http import JsonResponse

from rest_framework import status
from rest_framework.response import Response # Not woring with View
from rest_framework.views import APIView # Not woring properly : for get kwargs is {}

from .models import CompanyAccount
from . serializers import CompanyAccountSerializer


class CompanyAccountView(View):
    def get(self, request, *args, **kwargs):
        cmp_acc_id = request.GET.get('id')
        if cmp_acc_id:
            try:
                cmp_acc_obj = CompanyAccount.objects.get(id=cmp_acc_id)
                serializer = CompanyAccountSerializer(cmp_acc_obj)
                context = {"success": True, "data": serializer.data}
                return JsonResponse(context, status=status.HTTP_200_OK)
            except:
                context = {"success": False, "msg": "Please give valid company account id."}
                return JsonResponse(context, status=status.HTTP_404_NOT_FOUND)
            
        context = {"success": False, "msg": "Please give company account id."}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request, *args, **kwargs):
        serializer = CompanyAccountSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            context = {"success": True, "msg": "Company Acccount created successfully..!", "data": serializer.data}
            return JsonResponse(context, status=status.HTTP_201_CREATED)
        else:
            context = {"success": False, "msg": "Company Acccount creating failed..!", "error": serializer.errors}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)
