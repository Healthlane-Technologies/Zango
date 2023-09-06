from django.urls import re_path, path, include

from .views import BenefitView, BenefitGetView, BenefitRunView, DispensingOptionsView, RunScript


urlpatterns = [
    path("add_benefit/", BenefitView.as_view(), name="add_benefit"),
    path("get_benefit_details/", BenefitView.as_view(), name="get_benefit_details"),
    path("get_benefits/", BenefitGetView.as_view(), name="get_benefits"),
    path("test/", BenefitRunView.as_view(), name="test"),

    path("add_dispensig_option/", DispensingOptionsView.as_view(), name="add_dispensig_option"),
    path("get_dispensig_option/", DispensingOptionsView.as_view(), name="get_dispensig_option"),

    path("run/<int:id>/",RunScript.as_view(), name="run_script"),
    # path("run/",RunScript.as_view(), name="run_script"),

    # re_path(
    #     r'^run/(?P<id>\d+)/$',
    #     RunScript.as_view(),
    #     name='run_script'
    # )
]
