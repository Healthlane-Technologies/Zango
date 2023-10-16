from zelthy.core.api import get_api_response, ZelthyGenericPlatformAPIView
from zelthy.apps.tasks.models import AppTask
from zelthy.core.api.utils import ZelthyAPIPagination


class AppTaskView(ZelthyGenericPlatformAPIView, ZelthyAPIPagination):
    pagination_class = ZelthyAPIPagination

    def get(self, request, *args, **kwargs):
        try:
            app_task = AppTask.objects.all()
            paginated_tasks = self.paginate_queryset(app_task, request, view=self)

            serializer = AppTaskSerializer(app_task, many=True)
            success = True
            response = {
                "app_tasks": serializer.data,
                "message": "All app tasks fetched successfully",
            }
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500
