class RelaxedCSPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-eval' 'unsafe-inline' https://www.google.com https://www.gstatic.com https://www.recaptcha.net; "
            "frame-src https://www.google.com https://www.gstatic.com https://www.recaptcha.net; "
            "style-src 'self' 'unsafe-inline'; "
            "connect-src 'self' https://www.google.com https://www.gstatic.com https://www.recaptcha.net; "
            "img-src 'self' data: https://www.gstatic.com https://www.google.com;"
        )
        return response
