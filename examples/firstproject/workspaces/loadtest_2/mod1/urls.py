from django.urls import re_path

from .views import View1
from .views import View2
urlpatterns = [
    re_path(
        r'^view1/(?P<id>\d+)/$',
        View1.as_view(),
        name='view1'
    ),
    re_path(
        r'^view2/$',
        View2.as_view(),
        name="view2"
    )
]


