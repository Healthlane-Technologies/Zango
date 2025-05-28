"""
Internal HTTP Request Router

This module provides functionality to intercept and route HTTP requests internally
within a Zango application. It patches the standard requests library methods to
check if the requested domain is internal, and if so, processes the request using
Zango's request handling instead of making actual HTTP calls.
"""

import io
import json
import mimetypes

from importlib import import_module

import requests

from requests.cookies import extract_cookies_to_jar
from requests.models import Response
from requests.structures import CaseInsensitiveDict
from requests.utils import get_encoding_from_headers
from urllib3.response import HTTPResponse

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import connection
from django.http.response import HttpResponse
from django.template.response import ContentNotRenderedError
from django.test import RequestFactory


# Store original request methods for fallback
ORIGINAL_METHODS = {
    "post": requests.post,
    "get": requests.get,
    "put": requests.put,
    "delete": requests.delete,
}


def build_response(req, resp):
    """
    Build a requests.Response object from a urllib3.HTTPResponse.

    Args:
        req: The original request object
        resp: The urllib3 response object

    Returns:
        A requests.Response object
    """
    response = Response()
    response.status_code = getattr(resp, "status", None)
    response.headers = CaseInsensitiveDict(getattr(resp, "headers", {}))
    response.encoding = get_encoding_from_headers(response.headers)
    response.raw = resp
    response.reason = response.raw.reason

    if isinstance(req.url, bytes):
        response.url = req.url.decode("utf-8")
    else:
        response.url = req.url

    # Add new cookies from the server
    extract_cookies_to_jar(response.cookies, req, resp)
    response.request = req

    return response


def get_domain_from_url(url: str):
    """
    Extract and look up the domain object from a URL.

    Args:
        url: The URL to extract the domain from

    Returns:
        A domain object if found, otherwise None
    """
    from django_tenants.utils import get_tenant_domain_model, remove_www

    domain = url.split("://")[-1].split("/")[0]
    domain = remove_www(domain.split(":")[0])
    return get_tenant_domain_model().objects.filter(domain=domain).first()


def process_internal_request(request, tenant, **kwargs) -> HttpResponse:
    """
    Process an internal request using Django's request handling.

    Args:
        request: The Django request object
        tenant: The tenant object
        **kwargs: Additional keyword arguments

    Returns:
        A Django HttpResponse
    """
    original_tenant = connection.tenant

    request.tenant = tenant
    request.internal_routing = True
    connection.set_tenant(tenant)

    # Initialize workspace
    ws_module = import_module("zango.apps.dynamic_models.workspace.base")
    ws_klass = getattr(ws_module, "Workspace")
    ws = ws_klass(tenant, request)
    ws.ready()

    # Match and execute view
    view, resolve = ws.match_view(request)
    if not view:
        return HttpResponse(status=404)

    # Update kwargs with captured URL parameters
    captured_kwargs = getattr(resolve, "captured_kwargs", {})
    if captured_kwargs:
        kwargs.update(captured_kwargs)

    # Remove request-specific kwargs that shouldn't be passed to the view
    for key in ("data", "headers", "params", "files"):
        kwargs.pop(key, None)

    response = view(request, request.META["PATH_INFO"], **kwargs)
    connection.set_tenant(original_tenant)
    return response


def process_uploaded_files(request, files):
    """
    Process and add uploaded files to the request object.

    Args:
        request: The Django request object
        files: Files to process (list or dict)
    """
    if not files:
        return

    if isinstance(files, list):
        uploaded_files = {}
        for file_info in files:
            try:
                field_name, (file_name, file_obj, content_type) = file_info
            except ValueError:
                field_name, file_obj, content_type = file_info
                file_name = file_obj.name

            # Create an InMemoryUploadedFile object
            uploaded_file = create_in_memory_uploaded_file(
                file_obj, field_name, file_name, content_type
            )

            # Add the file to the dictionary
            if field_name in uploaded_files:
                uploaded_files[field_name].append(uploaded_file)
            else:
                uploaded_files[field_name] = [uploaded_file]

        # Add the files to request.FILES
        for field_name, file_list in uploaded_files.items():
            for file in file_list:
                request.FILES.appendlist(field_name, file)

    elif isinstance(files, dict):
        for field_name, file_obj in files.items():
            content_type = mimetypes.guess_type(file_obj.name)[0]
            uploaded_file = create_in_memory_uploaded_file(
                file_obj, field_name, file_obj.name, content_type
            )
            request.FILES[field_name] = uploaded_file


def create_in_memory_uploaded_file(file_obj, field_name, file_name, content_type):
    """
    Create an InMemoryUploadedFile from a file object.

    Args:
        file_obj: The file object
        field_name: Field name for the file
        file_name: Name of the file
        content_type: Content type of the file

    Returns:
        An InMemoryUploadedFile object
    """
    # Get file size by seeking to the end
    file_size = file_obj.seek(0, 2)
    # Reset the file pointer to the beginning
    file_obj.seek(0)

    return InMemoryUploadedFile(
        file=file_obj,
        field_name=field_name,
        name=file_name,
        content_type=content_type,
        size=file_size,
        charset=None,
    )


def create_django_request(method, url, **kwargs):
    """
    Create a Django request object from request parameters.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: The URL for the request
        **kwargs: Additional request parameters

    Returns:
        A Django request object
    """
    factory = RequestFactory()
    factory_method = getattr(factory, method.lower())

    data = kwargs.get("data", kwargs.get("json", {}))
    headers = kwargs.get("headers", {})

    # Process cookies
    cookies = kwargs.get("cookies", {})
    cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
    if not headers.get("cookies") and cookies:
        headers["Cookie"] = cookie_header

    # Extract content type
    content_type = headers.get("Content-Type")
    if isinstance(headers, dict):
        content_type = headers.pop("Content-Type", "") if headers else ""

    # Create request args
    req_args = {"path": url}
    if method.lower() in ("post", "put", "patch") and data:
        try:
            data = json.loads(data)
            content_type = "application/json"
        except Exception:
            pass
        req_args["data"] = data
    if headers:
        req_args["headers"] = headers
    if content_type:
        req_args["content_type"] = content_type

    return factory_method(**req_args)


def django_response_to_requests_response(
    django_response, request_obj, method, url, data=None, headers=None
):
    """
    Convert a Django HttpResponse to a requests.Response object.

    Args:
        django_response: The Django response object
        request_obj: The original request object
        method: HTTP method
        url: The request URL
        data: Request data
        headers: Request headers

    Returns:
        A requests.Response object
    """
    try:
        resp_body = django_response.content
    except ContentNotRenderedError:
        resp_body = getattr(django_response, "data", "")

    # Normalize response body to bytes
    if isinstance(resp_body, dict):
        resp_body = json.dumps(resp_body).encode("utf-8")
    elif isinstance(resp_body, str):
        resp_body = resp_body.encode("utf-8")
    elif not isinstance(resp_body, bytes):
        raise ValueError(f"Unknown response type: {type(resp_body)} returned")

    # Create urllib3 response
    urllib_response = HTTPResponse(
        body=io.BytesIO(resp_body),
        headers=django_response.headers,
        status=django_response.status_code,
        reason=getattr(django_response, "reason_phrase", ""),
        decode_content=False,
        preload_content=False,
    )

    # Create requests Request object
    req = requests.Request(method, url, data=data, headers=headers).prepare()

    # Build and return the response
    response = build_response(req, urllib_response)

    # Process cookies
    if hasattr(django_response, "cookies"):
        for cookie_name, cookie_obj in django_response.cookies.items():
            cookie_value = cookie_obj.value
            cookie_dict = {
                "value": cookie_value,
                "path": cookie_obj.get("path", "/"),
                "domain": cookie_obj.get("domain", None),
                "secure": cookie_obj.get("secure", False),
            }
            response.cookies.set(cookie_name, **cookie_dict)

    return response


def internal_request(method, url, **kwargs):
    """
    Process an HTTP request, routing internally if possible.

    Args:
        method: HTTP method (GET, POST, etc.)
        url: The URL for the request
        **kwargs: Additional request parameters

    Returns:
        A requests.Response object
    """
    domain_obj = get_domain_from_url(url)
    if not domain_obj:
        # If domain is not internal, use the original request method
        return ORIGINAL_METHODS[method.lower()](url, **kwargs)

    # Get tenant from domain
    tenant = domain_obj.tenant

    # Create Django request
    django_request = create_django_request(method, url, **kwargs)

    # Process uploaded files if any
    process_uploaded_files(django_request, kwargs.get("files", {}))

    # Process internal request
    django_response = process_internal_request(django_request, tenant, **kwargs)

    # Convert Django response to requests.Response
    return django_response_to_requests_response(
        django_response,
        django_request,
        method,
        url,
        data=kwargs.get("data", {}),
        headers=kwargs.get("headers", {}),
    )


def internal_request_get(url, **kwargs):
    return internal_request("GET", url, **kwargs)


def internal_request_post(url, **kwargs):
    return internal_request("POST", url, **kwargs)


def internal_request_put(url, **kwargs):
    return internal_request("PUT", url, **kwargs)


def internal_request_delete(url, **kwargs):
    return internal_request("DELETE", url, **kwargs)


# Patch the requests library methods
requests.get = internal_request_get
requests.post = internal_request_post
requests.put = internal_request_put
requests.delete = internal_request_delete
