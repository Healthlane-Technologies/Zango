from django.urls import re_path
from .views import view1
from .views import View2
from .views import new_view
from .views import foreign_view

urlpatterns = [
    
    re_path(
        r'^view1/(?P<id>\d+)/',
        view1,
        name='view1'
    ),
    re_path(
        r'^view2/(?P<id>\d+)/(?P<uuid>[\w-]+)/$',
        View2.as_view(),
        name='view1'
    ),
    re_path(
        r'^view3/$',
        new_view,
        name="new_view"
    ),
    re_path(
        r'^view-foreign/$',
        foreign_view,
        name="foreign_view"
    )
]

