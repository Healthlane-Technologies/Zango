import json

from rest_framework.views import APIView

from zango.core.api import get_api_response


class GenericORMView(APIView):

    model = None
    serializer = None

    def postprocess_get(self, queryset):
        return queryset

    def postprocess_post(self, object):
        return object

    def postprocess_put(self, object):
        return object

    def postprocess_delete(self):
        pass

    def get(self, request, *args, **kwargs):
        try:
            filters = json.loads(request.GET.get("filters", "{}"))
            qargs = json.loads(request.GET.get("qargs", "{}"))
            queryset = self.model.objects.filter(**filters)
            queryset = queryset.filter(**qargs)
            distinct = request.GET.get("distinct", None)
            first = request.GET.get("first", None)
            order_by = request.GET.get("order_by", None)
            if order_by:
                queryset = queryset.order_by(order_by)
            if distinct:
                queryset = queryset.distinct()
            if first:
                queryset = queryset.first()
            queryset = self.postprocess_get(queryset)
            serializer = self.serializer(queryset, many=True)
            return get_api_response(True, serializer.data, 200)
        except Exception as e:
            import traceback

            traceback.print_exc()
            return get_api_response(False, str(e), 400)

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            obj = self.model(**data)
            obj.save()
            obj = self.postprocess_post(obj)
            obj.save()
            serializer = self.serializer(obj)
            return get_api_response(True, serializer.data, 200)
        except Exception as e:
            import traceback

            traceback.print_exc()
            return get_api_response(False, str(e), 400)

    def put(self, request, *args, **kwargs):
        data = request.data
        pk = request.PUT.get("pk", None)
        if pk:
            obj = self.model.objects.get(pk=pk)
            obj.update(**data)
            obj.save()
            obj = self.postprocess_put(obj)
            serializer = self.serializer(obj)
            return get_api_response(True, serializer.data, 200)
        return get_api_response(False, "No pk found", 400)

    def delete(self, request, *args, **kwargs):
        pk = request.GET.get("pk", None)
        if pk:
            self.model.objects.get(pk=pk).delete()
        self.postprocess_delete()
        return get_api_response(True, "deleted", 200)
