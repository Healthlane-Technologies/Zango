from django.urls import re_path
from .views import AppLandingPageView
from .views import app_landing


urlpatterns = [
    
    re_path(
        r'^$',
        AppLandingPageView.as_view(),
        name='landingPage'
    ),
    re_path(
        r'^func/$',
        app_landing,
        name='funclanding' 
    )
    
    ]