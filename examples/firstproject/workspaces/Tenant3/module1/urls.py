from django.urls import re_path

from .views import View2
# print(View2)
urlpatterns = [
    
    # re_path(
    #     r'^view1/(?P<id>\d+)/',
    #     view1,
    #     name='view1'
    # ),
    re_path(
        r'^view2/(?P<id>\d+)/$',
        View2.as_view(),
        name='view1'
    ),
]


# code update in a workspace => 