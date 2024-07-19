import os


def otel_is_enabled():
    """Returns True if env var OTEL_IS_ENABLED is set to any non 
    blank string
    """
    return os.getenv("OTEL_IS_ENABLED", False)
    
def otel_export_to_otlp():
    """Returns True if env var OTEL_EXPORT_TO_OTLP is set to any non 
    blank string
    """
    return os.getenv("OTEL_EXPORT_TO_OTLP", False)

def otel_otlp_endpoint():
    return str(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"))

def otel_otlp_headers():
    return str(os.getenv("OTEL_EXPORTER_OTLP_HEADERS", ""))

def otel_otlp_protocol():
    return str(os.getenv("OTEL_EXPORTER_PROTOCOL", ""))

def otel_resource_name():
    return str(os.getenv("OTEL_RESOURCE_NAME", "Zango"))
    