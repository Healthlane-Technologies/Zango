import json
from collections import OrderedDict

from django.http import HttpResponse
from rest_framework.pagination import PageNumberPagination


class ZelthyAPIPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response_data(self, data):
        return OrderedDict(
            [
                ("total_records", self.page.paginator.count),
                ("total_pages", self.page.paginator.num_pages),
                ("next", self.get_next_link()),
                ("previous", self.get_previous_link()),
                ("records", data),
            ]
        )


def get_api_response(success, response_content, status):
    response = {"success": success, "response": response_content}

    return HttpResponse(json.dumps(response), status=status)
