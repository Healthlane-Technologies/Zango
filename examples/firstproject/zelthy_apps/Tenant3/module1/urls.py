from django.urls import re_path
from .views import view1
from .views import View2

urlpatterns = [
    
    re_path(
        r'^view1/(?P<id>\d+)/',
        view1,
        name='view1'
    ),
    re_path(
        r'^view2/(?P<id>\d+)/$',
        View2.as_view(),
        name='view1'
    ),
]

