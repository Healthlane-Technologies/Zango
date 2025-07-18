class TenantMixin:
    def get_tenant(self, **kwargs):
        from zango.apps.shared.tenancy.models import TenantModel

        obj = TenantModel.objects.get(uuid=kwargs.get("app_uuid"))
        return obj
