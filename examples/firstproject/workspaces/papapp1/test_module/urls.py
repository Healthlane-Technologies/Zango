from django.urls import re_path, path, include

from .views import TestView, AddSystemDetails
urlpatterns = [
    
    # re_path(
    #     r'^test/$',
    #     TestView.as_view(),
    #     name='testview'
    # ),
    # path("add_data/", AddSystemDetails.as_view(), name="add_details"),
    # path("save_data/", AddSystemDetails.as_view(), name="add_details"),
    # path("get_data/", AddSystemDetails.as_view(), name="get_data"),

    re_path(
        r'^add_data/$',
        AddSystemDetails.as_view(),
        name="add_details"
    ),
    # re_path(
    #     r'^get_data/$',
    #     AddSystemDetails.as_view(),
    #     name="get_details"
    # ),


    # re_path(
    #     r'^get_data/(?P<id>\d+)/$',
    #     AddSystemDetails.as_view(),
    #     name='get_data'
    # )

]

# TODO define url in way


# path("get_data/<int:id>/", AddSystemDetails.as_view(), name="get_data"),