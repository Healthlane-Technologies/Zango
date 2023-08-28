from django.views import View
from django.http import JsonResponse

from rest_framework import status
from rest_framework.response import Response # Not woring with View
from rest_framework.views import APIView # Not woring properly : for get kwargs is {}

from .models import SkuModel, SkuTypes, OrderItemsModel, DispensingOptionsModel, BenefitsSupplyChainNodes
from .serializers import SkuModelSerializer, SkuTypeSerializer, OrderItemsModelSerializer


class SkuView(View):
    def get(self, request, *args, **kwargs):
        _id = request.GET.get('id')
        if _id:
            try:
                _obj = SkuModel.objects.get(id=_id)
                serializer = SkuModelSerializer(_obj)
                context = {"success": True, "data": serializer.data}
                return JsonResponse(context, status=status.HTTP_200_OK)
            except:
                context = {"success": False, "msg": "Please give valid sku id."}
                return JsonResponse(context, status=status.HTTP_404_NOT_FOUND)
            
        context = {"success": False, "msg": "Please give sku id."}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request, *args, **kwargs):
        serializer = SkuModelSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            context = {"success": True, "msg": "Sku addedd successfully..!", "data": serializer.data}
            return JsonResponse(context, status=status.HTTP_201_CREATED)
        else:
            context = {"success": False, "msg": "Sku addedd failed..!", "error": serializer.errors}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)
    

class SkuTypesView(View):
    def get(self, request, *args, **kwargs):
        _id = request.GET.get('id')
        if _id:
            try:
                _obj = SkuTypes.objects.get(id=_id)
                serializer = SkuTypeSerializer(_obj)
                context = {"success": True, "data": serializer.data}
                return JsonResponse(context, status=status.HTTP_200_OK)
            except:
                context = {"success": False, "msg": "Please give valid sku type id."}
                return JsonResponse(context, status=status.HTTP_404_NOT_FOUND)
            
        context = {"success": False, "msg": "Please give sku type id."}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request, *args, **kwargs):
        serializer = SkuTypeSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            context = {"success": True, "msg": "Sku type addedd successfully..!", "data": serializer.data}
            return JsonResponse(context, status=status.HTTP_201_CREATED)
        else:
            context = {"success": False, "msg": "Sku type addedd failed..!", "error": serializer.errors}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)
    

class OrderItemsView(View):
    def get(self, request, *args, **kwargs):
        _id = request.GET.get('id')
        if _id:
            try:
                _obj = OrderItemsModel.objects.get(id=_id)
                serializer = OrderItemsModelSerializer(_obj)
                context = {"success": True, "data": serializer.data}
                return JsonResponse(context, status=status.HTTP_200_OK)
            except:
                context = {"success": False, "msg": "Please give valid ordet item id."}
                return JsonResponse(context, status=status.HTTP_404_NOT_FOUND)
            
        context = {"success": False, "msg": "Please give ordet item id."}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request, *args, **kwargs):
        serializer = OrderItemsModelSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            context = {"success": True, "msg": "order item addedd successfully..!", "data": serializer.data}
            return JsonResponse(context, status=status.HTTP_201_CREATED)
        else:
            context = {"success": False, "msg": "order item addedd failed..!", "error": serializer.errors}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)


