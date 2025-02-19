class TokenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.headers.get("Authorization"):
            request.csrf_processing_done = True
        response = self.get_response(request)
        return response
