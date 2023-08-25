from django.urls import re_path, path, include

from .views import CompanyAccountView


urlpatterns = [
    path("add_company_account/", CompanyAccountView.as_view(), name="add_company_account"),
    path("get_company_account_details/<int:id>/", CompanyAccountView.as_view(), name="get_company_account_details")
]
