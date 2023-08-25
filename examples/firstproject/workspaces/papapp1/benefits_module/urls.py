from django.urls import re_path, path, include

from .views import BenefitView, BenefitGetView, BenefitRunView


urlpatterns = [
    path("add_benefit/", BenefitView.as_view(), name="add_benefit"),
    path("get_benefit_detials/", BenefitView.as_view(), name="get_benefit_detials"),
    path("get_benefits/", BenefitGetView.as_view(), name="get_benefits"),
    path("test/", BenefitRunView.as_view(), name="test")
]
