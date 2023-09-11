from django.urls import re_path

from .views import FrameTestView

urlpatterns = [
    
    re_path(
        r'^frame-test/$',
        FrameTestView.as_view(),
        name='frame-test'
    ),
]

