# -*- coding: utf-8 -*-

from django.shortcuts import render


def zelthyhttp404handler(request, exception, template_name="exceptions/404.html"):
    """
    Custom 404 handler
    """
    response = render(request, template_name)
    response.status_code = 404
    return response


def zelthyhttp500handler(request):
    """
    Custom 500 handler
    """
    return render(request, "exceptions/500.html")


def zelthyhttp403handler(request, exception, template_name="exceptions/403.html"):
    """
    Custom 403 handler
    """
    return render(request, template_name)


def zelthycsrftokenhandler(request, reason=""):
    """
    Custom 403 handler
    """
    return render(request, "exceptions/csrf_token_error.html")