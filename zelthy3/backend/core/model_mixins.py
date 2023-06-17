from django.db import models


class FullAuditMixin(models.Model):

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=255, blank=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(max_length=255, blank=True, editable=False)


    class Meta:
        abstract = True

    # def get_localized_datetime(self, dt):
    #     from django.db import connection
    #     import pytz
    #     tz = pytz.timezone(connection.tenant.tenant_config.timezone)
    #     if dt:
    #         return dt.astimezone(tz)
    #     return dt



