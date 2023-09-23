from django.urls import re_path

from .views import FrameTestView, CrudTestView

urlpatterns = [
    
    re_path(
        r'^frame-test/$',
        FrameTestView.as_view(),
        name='frame-test'
    ),
    re_path(
        r'^crud-test/$',
        CrudTestView.as_view(),
        name='crud-test'
    )
]

