from opentelemetry import trace


class OtelZangoContextMiddleware:
    """A middleware to update the otel span name for requests
    made to tenants. Adds the context of the tenant and replaces
    route with the path_info, as all tenant routes are wildcard
    route at Django level
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Get the current span from the tracer
        span = trace.get_current_span()

        if span:
            if request.tenant.tenant_type == "app":
                span_name = (
                    f"{request.tenant.name}-{request.method} {request.path_info}"
                )
            else:
                span_name = f"platform-{request.method} {request.resolver_match.route}"
            span.update_name(span_name)
