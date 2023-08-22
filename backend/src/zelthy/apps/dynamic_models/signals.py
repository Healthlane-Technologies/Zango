from django.dispatch import Signal

tenant_updated = Signal(providing_args=["tenant_name"])
