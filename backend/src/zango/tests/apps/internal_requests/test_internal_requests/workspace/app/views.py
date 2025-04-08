from rest_framework.views import APIView
from django.http import JsonResponse
from django.views import View

from zango.core.utils import get_current_request_url
from django.http import HttpResponse

import requests

COOKIE = "cookie_name"
COOKIE_VALUE = "cookie_value"

JSON_DATA = {
    "field_1": "value_1",
    "field_2": "value_2"
}

GET_HEADERS = {
    "Accept": "text/plain"
}

POST_HEADERS = {
    "Content-Type": "application/json"
}

PUT_HEADERS = {
    "Cache-Control": "no-cache",
    "Content-Type": "application/json"
}

DELETE_HEADERS = {
    "Authorization": "Bearer test-token"
}

QUERY_PARAM = "name"
PARAM_VALUE = "zango"

PATH_PARAM = "PTH"

from django.http import JsonResponse
from django.views import View

class TestPathParamView(View):
    def get(self, request, *args, **kwargs):
        if kwargs.get("param") != PATH_PARAM:
            raise Exception("PATH param missing")
        return JsonResponse({'param': 'present'})

    def post(self, request, *args, **kwargs):
        if kwargs.get("param") != PATH_PARAM:
            raise Exception("PATH param missing")
        return JsonResponse({'param': 'present'})

    def put(self, request, *args, **kwargs):
        if kwargs.get("param") != PATH_PARAM:
            raise Exception("PATH param missing")
        return JsonResponse({'param': 'present'})

    def delete(self, request, *args, **kwargs):
        if kwargs.get("param") != PATH_PARAM:
            raise Exception("PATH param missing")
        return JsonResponse({'param': 'present'})

class TestREPathView(View):
    def get(self, request, *args, **kwargs):
        if kwargs.get("param") != PATH_PARAM:
            raise Exception("PATH param missing")
        return JsonResponse({'param': 'present'})

    def post(self, request, *args, **kwargs):
        if kwargs.get("param") != PATH_PARAM:
            raise Exception("PATH param missing")
        return JsonResponse({'param': 'present'})

    def put(self, request, *args, **kwargs):
        if kwargs.get("param") != PATH_PARAM:
            raise Exception("PATH param missing")
        return JsonResponse({'param': 'present'})

    def delete(self, request, *args, **kwargs):
        if kwargs.get("param") != PATH_PARAM:
            raise Exception("PATH param missing")
        return JsonResponse({'param': 'present'})

class TestAPIView(APIView):
    def get(self, request, *args, **kwargs):
        action = request.GET.get("action")
        if action == "headers":
            if request.headers.get("Accept") != GET_HEADERS.get("Accept"):
                raise Exception("Accept Header not found")
        
        if action == "query_params":
            if not request.GET.get(QUERY_PARAM) == PARAM_VALUE:
                raise Exception("Query param not found")
            
        if action == "cookie":
            if not request.COOKIES.get(COOKIE):
                raise Exception("Cookie not found")
            if request.COOKIES[COOKIE] != COOKIE_VALUE:
                raise Exception("Cookie value is not the same")
        
        if action == "response_cookie":
            resp = JsonResponse({"Message": "Setting Cookie"})
            resp.set_cookie(COOKIE, COOKIE_VALUE)
            return resp

        return JsonResponse({"message": "GET request received"})

    def post(self, request, *args, **kwargs):
        action = request.GET.get("action")
        if action == "headers":
            if request.headers.get("Content-Type") != POST_HEADERS.get("Content-Type"):
                raise Exception("Content-Type Header not found")
        
        if action == "query_params":
            if not request.POST.get(QUERY_PARAM) == PARAM_VALUE:
                raise Exception("Query param not found")
        
        if action == "cookie":
            if not request.COOKIES.get(COOKIE):
                raise Exception("Cookie not found")
            if request.COOKIES[COOKIE] != COOKIE_VALUE:
                raise Exception("Cookie value is not the same")
        
        if action == "response_cookie":
            resp = JsonResponse({"Message": "Setting Cookie"})
            resp.set_cookie(COOKIE, COOKIE_VALUE)
            return resp
        
        return JsonResponse({"message": "POST request received."})

    def put(self, request, *args, **kwargs):
        action = request.GET.get("action")
        if action == "headers":
            if request.headers.get("Cache-Control") != PUT_HEADERS.get("Cache-Control"):
                raise Exception("Cache-Control Header not found")
        
        if action == "query_params":
            if not request.PUT.get(QUERY_PARAM) == PARAM_VALUE:
                raise Exception("Query param not found")
        
        if action == "cookie":
            if not request.COOKIES.get(COOKIE):
                raise Exception("Cookie not found")
            if request.COOKIES[COOKIE] != COOKIE_VALUE:
                raise Exception("Cookie value is not the same")
        
        if action == "response_cookie":
            resp = JsonResponse({"Message": "Setting Cookie"})
            resp.set_cookie(COOKIE, COOKIE_VALUE)
            return resp
        
        return JsonResponse({"message": "PUT request received."})

    def delete(self, request, *args, **kwargs):
        action = request.GET.get("action")
        if action == "headers":
            if request.headers.get("Authorization") != DELETE_HEADERS.get("Authorization"):
                raise Exception("Authorization Header not found")
        
        if action == "query_params":
            if not request.GET.get(QUERY_PARAM) == PARAM_VALUE:
                raise Exception("Query param not found")
        
        if action == "cookie":
            if not request.COOKIES.get(COOKIE):
                raise Exception("Cookie not found")
            if request.COOKIES[COOKIE] != COOKIE_VALUE:
                raise Exception("Cookie value is not the same")
        
        if action == "response_cookie":
            resp = JsonResponse({"Message": "Setting Cookie"})
            resp.set_cookie(COOKIE, COOKIE_VALUE)
            return resp
        
        return JsonResponse({"message": "DELETE request received."})

class TestDataView(View):
    
    def post(self, request, *args, **kwargs):
        action = request.GET.get("action", "")
        if action =="json_data":
            if request.data.get("field_1") != JSON_DATA["field_1"] or request.data.get("field_2") != JSON_DATA["field_2"]:
                raise Exception ("JSON data missing")
        return JsonResponse({"message": "Data correctly passed"})

    def put(self, request, *args, **kwargs):
        action = request.GET.get("action", "")
        if action =="json_data":
            if request.data.get("field_1") != JSON_DATA["field_1"] or request.data.get("field_2") != JSON_DATA["field_2"]:
                raise Exception ("JSON data missing")
        return JsonResponse({"message": "Data correctly passed"})
    
class TestView(View):
    
    def post(self, request, *args, **kwargs):
        url = f"{get_current_request_url(request)}/app/api/"

        action = request.GET.get("action", "")

        # Test Headers
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

        # Test Path Param

        url = f"{get_current_request_url(request)}/app/path/{PATH_PARAM}/"
        
        if action == "get_path_params":
            resp = requests.get(f"{url}")
            return HttpResponse(resp.content)
            
        if action == "post_path_params":
            resp = requests.post(f"{url}", headers=POST_HEADERS)
            return HttpResponse(resp.content)
            
        if action == "put_path_params":
            resp = requests.put(f"{url}", headers=PUT_HEADERS)
            return HttpResponse(resp.content)
            
        if action == "delete_path_params":
            resp = requests.delete(f"{url}", headers=DELETE_HEADERS)
            return HttpResponse(resp.content)
        

        # Test RE Path Param
        url = f"{get_current_request_url(request)}/app/re_path/{PATH_PARAM}/"
        
        if action == "get_re_path_params":
            resp = requests.get(f"{url}")
            return HttpResponse(resp.content)
            
        if action == "post_re_path_params":
            resp = requests.post(f"{url}", headers=POST_HEADERS)
            return HttpResponse(resp.content)
            
        if action == "put_re_path_params":
            resp = requests.put(f"{url}", headers=PUT_HEADERS)
            return HttpResponse(resp.content)
            
        if action == "delete_re_path_params":
            resp = requests.delete(f"{url}", headers=DELETE_HEADERS)
            return HttpResponse(resp.content)
        
        # Test Cookie

        url = f"{get_current_request_url(request)}/app/api/"
        
        if action == "get_cookie":
            resp = requests.get(f"{url}?action=cookie", cookies={COOKIE: COOKIE_VALUE})
            return HttpResponse(resp.content)
            
        if action == "post_cookie":
            resp = requests.post(f"{url}?action=cookie", headers=POST_HEADERS, cookies={COOKIE: COOKIE_VALUE})
            return HttpResponse(resp.content)
            
        if action == "put_cookie":
            resp = requests.put(f"{url}?action=cookie", headers=PUT_HEADERS, cookies={COOKIE: COOKIE_VALUE})
            return HttpResponse(resp.content)
            
        if action == "delete_cookie":
            resp = requests.delete(f"{url}?action=cookie", headers=DELETE_HEADERS, cookies={COOKIE: COOKIE_VALUE})
            return HttpResponse(resp.content)
        
        # Test JSON Data

        url = f"{get_current_request_url(request)}/app/data/"
            
        if action == "post_json_data":
            resp = requests.post(f"{url}?action=json_data", headers=POST_HEADERS, data=JSON_DATA)
            return HttpResponse(resp.content)
            
        if action == "put_json_data":
            resp = requests.put(f"{url}?action=json_data", headers=PUT_HEADERS, data=JSON_DATA)
            return HttpResponse(resp.content)
        
        # Test Response Cookie

        url = f"{get_current_request_url(request)}/app/api/"
        
        if action == "get_response_cookie":
            resp = requests.get(f"{url}?action=response_cookie")
            if not resp.cookies.get(COOKIE) == COOKIE_VALUE:
                return HttpResponse("Cookie not found in response", status=500)
            return HttpResponse(resp.content)
            
        if action == "post_response_cookie":
            resp = requests.post(f"{url}?action=response_cookie", headers=POST_HEADERS)
            if not resp.cookies.get(COOKIE) == COOKIE_VALUE:
                return HttpResponse("Cookie not found in response", status=500)
            return HttpResponse(resp.content)
            
        if action == "put_response_cookie":
            resp = requests.put(f"{url}?action=response_cookie", headers=PUT_HEADERS)
            if not resp.cookies.get(COOKIE) == COOKIE_VALUE:
                return HttpResponse("Cookie not found in response", status=500)
            return HttpResponse(resp.content)
            
        if action == "delete_response_cookie":
            resp = requests.delete(f"{url}?action=response_cookie", headers=DELETE_HEADERS)
            if not resp.cookies.get(COOKIE) == COOKIE_VALUE:
                return HttpResponse("Cookie not found in response",  status=500)
            return HttpResponse(resp.content)

        resp = requests.get(url)
        resp.raise_for_status()
        return HttpResponse("Internal requests working")
