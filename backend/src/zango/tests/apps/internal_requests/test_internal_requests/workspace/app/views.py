import json
import os

from rest_framework.views import APIView
from django.http import JsonResponse
from django.views import View

from zango.core.utils import get_current_request_url
from django.http import HttpResponse

import requests

COOKIE = "cookie_name"
COOKIE_VALUE = "cookie_value"

FILE_NAME = "test1.txt"
FILE_NAME_1 = "test2.txt"
FILE_DIR = os.path.join(os.path.dirname(__file__), "files")

FORM_DATA_MULTIPART = {
    "field_1": "value_1",
    "field_2": "value_2"
}



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
        if not action:
            raise Exception("Action not found")
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
        if not action:
            raise Exception("Action not found")
        if action == "headers":
            if request.headers.get("Content-Type") != POST_HEADERS.get("Content-Type"):
                raise Exception("Content-Type Header not found")
        
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
        
        if action =="json_data":
            if request.data.get("field_1") != JSON_DATA["field_1"] or request.data.get("field_2") != JSON_DATA["field_2"]:
                raise Exception ("JSON data missing")
        
        if action == "file":
            uploaded_file = request.FILES.get(FILE_NAME)

            if not uploaded_file:
                raise Exception(f"File not found in the request.")
            
            # Optionally, you can perform additional checks on the file, such as its content or size
            if uploaded_file.name != FILE_NAME:
                raise Exception(f"Uploaded file name '{uploaded_file.name}' does not match the expected file name '{FILE_NAME}'.")
        
        if action == "multiple_files":
            uploaded_files = request.FILES.getlist('file')

            if not uploaded_files:
                raise Exception("No files found in the request.")
            
            if len(uploaded_files) != 2:
                raise Exception("Expected 2 files, but found {}".format(len(uploaded_files)))
        
        if action == "form_data_multipart":
            if request.POST.get("field_1") != FORM_DATA_MULTIPART["field_1"] or request.POST.get("field_2") != FORM_DATA_MULTIPART["field_2"]:
                raise Exception ("Multipart Form data missing")
        
        return JsonResponse({"message": "POST request received."})

    def put(self, request, *args, **kwargs):
        action = request.GET.get("action")
        if not action:
            raise Exception("Action not found")
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
        
        if action =="json_data":
            if request.data.get("field_1") != JSON_DATA["field_1"] or request.data.get("field_2") != JSON_DATA["field_2"]:
                raise Exception ("JSON data missing")
        
        if action == "form_data_multipart":
            if request.POST.get("field_1") != FORM_DATA_MULTIPART["field_1"] or request.POST.get("field_2") != FORM_DATA_MULTIPART["field_2"]:
                raise Exception ("Multipart Form data missing")
        
        return JsonResponse({"message": "PUT request received."})

    def delete(self, request, *args, **kwargs):
        action = request.GET.get("action")
        if not action:
            raise Exception("Action not found")
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
        
        return JsonResponse({"message": "DELETE request received."})

class TestDataView(View):

    def validate_json_data(self, request):
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return None, JsonResponse({"error": "Invalid JSON"}, status=400)

        if data.get("field_1") != JSON_DATA["field_1"] or data.get("field_2") != JSON_DATA["field_2"]:
            return None, JsonResponse({"error": "JSON data missing or incorrect"}, status=400)

        return data, None

    def post(self, request, *args, **kwargs):
        if request.GET.get("action") == "json_data":
            _, error_response = self.validate_json_data(request)
            if error_response:
                return error_response
        return JsonResponse({"message": "Data correctly passed"})

    def put(self, request, *args, **kwargs):
        if request.GET.get("action") == "json_data":
            _, error_response = self.validate_json_data(request)
            if error_response:
                return error_response
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
        
        # Test JSON Data in APIView

        url = f"{get_current_request_url(request)}/app/api/"
            
        if action == "post_json_data_api_view":
            resp = requests.post(f"{url}?action=json_data", headers=POST_HEADERS, data=JSON_DATA)
            return HttpResponse(resp.content)
            
        if action == "put_json_data_api_view":
            resp = requests.put(f"{url}?action=json_data", headers=PUT_HEADERS, data=JSON_DATA)
            return HttpResponse(resp.content)
        
        # Test File

        url = f"{get_current_request_url(request)}/app/api/"

        FILES = [
            ("file", open(os.path.join(FILE_DIR, FILE_NAME), "rb"), "text/plain"),
            ("file", open(os.path.join(FILE_DIR, FILE_NAME_1), "rb"), "text/plain"),
        ]

        if action == "post_file":
            resp = requests.post(f"{url}?action=file", files={FILE_NAME: open(os.path.join(FILE_DIR, FILE_NAME), "rb")}, headers={"Content-Type": "multipart/form-data; boundary=---011000010111000001101001"})
            return HttpResponse(resp.content)
        

        #Test Multiple Files

        if action == "post_multiple_files":
            resp = requests.post(f"{url}?action=multiple_files", files=FILES, headers={"Content-Type": "multipart/form-data; boundary=---011000010111000001101001"})
            return HttpResponse(resp.content)

        # Test Form Data Multipart

        if action == "post_form_data_multipart":
            resp = requests.post(f"{url}?action=form_data_multipart", data=FORM_DATA_MULTIPART)
            return HttpResponse(resp.content)
        
        if action == "put_form_data_multipart":
            resp = requests.put(f"{url}?action=form_data_multipart", data=FORM_DATA_MULTIPART)
            return HttpResponse(resp.content)
        return HttpResponse("Internal requests working")
