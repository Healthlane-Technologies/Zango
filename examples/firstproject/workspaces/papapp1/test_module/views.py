from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view


from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from .models import SystemDetails

from .serializers import SystemDetailsSerializers



def get_fun(request, id):
    print("id inside get_fun ===> ", id)
    print("request.GET ==> ", request.GET)
    print("kwargs ==> ")
    return JsonResponse({"success": True, "id": id})


class MyView(View):
    def get(self, request,id, *args, **kwargs):
        print("kwargs", kwargs)
        print("request.GET ==> ", request.GET)
        return JsonResponse({"success": True, "id": id})


class TestView(TemplateView):
    template_name = "home.html"




class AddSystemDetails(View):

    def post(self, request, *args, **kwargs):
        serializer = SystemDetailsSerializers(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            context = {"success": True, "msg": "Data inserted successfully..!"}
            # raise Exception("testing")
            return JsonResponse(context, status=status.HTTP_201_CREATED)
        else:
            context = {"success": False, "msg": serializer.errors}
        return JsonResponse(context, status=status.HTTP_400_BAD_REQUEST)
    

    def get(self, request, *args, **kwargs):
        _id=request.GET.get('id')
        if _id:
            data=SystemDetails.objects.filter(id=_id)
        else:
            data=SystemDetails.objects.all()
        serializer = SystemDetailsSerializers(data, many=True)
        return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)
    




# class AddSystemDetails(APIView):
#     # Apply @method_decorator to disable CSRF protection for the specific view
#     # @method_decorator(csrf_exempt)
#     # def dispatch(self, *args, **kwargs):
#     #     return super().dispatch(*args, **kwargs)

#     def post(self, request):
#         serializer = SystemDetailsSerializers(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             context = {"success": True, "msg": "Data inserted successfully..!", }
#             return Response(context, status.HTTP_201_CREATED)
#         else:
#             context = {"success": False, "msg": serializer.errors}
#         return Response(context, status.HTTP_400_BAD_REQUEST)
    

