from rest_framework.views import APIView
from django.http import JsonResponse
from django.views import View

from zango.core.utils import get_current_request_url
from django.http import HttpResponse

import requests

GET_HEADERS = {
    "Accept": "text/plain"
}

POST_HEADERS = {
    "Content-Type": "application/json"
}

PUT_HEADERS = {
    "Cache-Control": "no-cache"
}

DELETE_HEADERS = {
    "Authorization": "Bearer test-token"
}

QUERY_PARAM = "name"
PARAM_VALUE = "zango"

class TestAPIView(APIView):
    def get(self, request, *args, **kwargs):
        action = request.GET.get("action")
        if action == "headers":
            if request.headers.get("Accept") != GET_HEADERS.get("Accept"):
                raise Exception("Accept Header not found")
        
        if action == "query_params":
            if not request.GET.get(QUERY_PARAM) == PARAM_VALUE:
                raise Exception("Query param not found")
        
        return JsonResponse({"message": "GET request received"})

    def post(self, request, *args, **kwargs):
        action = request.GET.get("action")
        if action == "headers":
            if request.headers.get("Content-Type") != POST_HEADERS.get("Content-Type"):
                raise Exception("Content-Type Header not found")
        
        if action == "query_params":
            if not request.POST.get(QUERY_PARAM) == PARAM_VALUE:
                raise Exception("Query param not found")
        
        return JsonResponse({"message": "POST request received."})

    def put(self, request, *args, **kwargs):
        action = request.GET.get("action")
        if action == "headers":
            if request.headers.get("Cache-Control") != PUT_HEADERS.get("Cache-Control"):
                raise Exception("Cache-Control Header not found")
        
        if action == "query_params":
            if not request.PUT.get(QUERY_PARAM) == PARAM_VALUE:
                raise Exception("Query param not found")
        
        return JsonResponse({"message": "PUT request received."})

    def delete(self, request, *args, **kwargs):
        action = request.GET.get("action")
        if action == "headers":
            if request.headers.get("Authorization") != DELETE_HEADERS.get("Authorization"):
                raise Exception("Authorization Header not found")
        
        if action == "query_params":
            if not request.GET.get(QUERY_PARAM) == PARAM_VALUE:
                raise Exception("Query param not found")
        
        return JsonResponse({"message": "DELETE request received."})
    
class TestView(View):
    
    def post(self, request, *args, **kwargs):
        url = f"{get_current_request_url(request)}/app/api/"

        action = request.POST.get("action", "")

        if action == "get_headers":
            resp = requests.get(f"{url}/?action=headers", headers=GET_HEADERS)
            return HttpResponse(resp.content)
        
        if action == "post_headers":
            resp = requests.post(f"{url}/?action=headers", headers=POST_HEADERS)
            return HttpResponse(resp.content)
        
        if action == "put_headers":
            resp = requests.put(f"{url}/?action=headers", headers=PUT_HEADERS)
            return HttpResponse(resp.content)
            
        if action == "delete_headers":
            resp = requests.delete(f"{url}/?action=headers", headers=DELETE_HEADERS)
            return HttpResponse(resp.content)
        
            
        # Test query parameters
        if action == "get_query_params":
            resp = requests.get(f"{url}/?{QUERY_PARAM}={PARAM_VALUE}&action=query_params")
            return HttpResponse(resp.content)
            
        if action == "post_query_params":
            resp = requests.post(f"{url}/?{QUERY_PARAM}={PARAM_VALUE}&action=query_params", headers=POST_HEADERS)
            return HttpResponse(resp.content)
            
        if action == "put_query_params":
            resp = requests.put(f"{url}/?{QUERY_PARAM}={PARAM_VALUE}&action=query_params", headers=PUT_HEADERS)
            return HttpResponse(resp.content)
            
        if action == "delete_query_params":
            resp = requests.delete(f"{url}/?{QUERY_PARAM}={PARAM_VALUE}&action=query_params", headers=DELETE_HEADERS)
            return HttpResponse(resp.content)

        resp = requests.get(url)
        resp.raise_for_status()
        return HttpResponse("Internal requests working")
