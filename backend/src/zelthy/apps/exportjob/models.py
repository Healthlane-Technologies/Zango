from django.db import models


class ExportJob(models.Model):
    requested_by = models.ForeignKey(
        "appauth.AppUserModel", on_delete=models.DO_NOTHING, related_name="export_jobs"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=255)

    class Meta:
        abstract = True