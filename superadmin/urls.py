from django.urls import path
from .views import SuperadminLoginView, SuperadminDetailAPI

urlpatterns=[
    path('login_sa/', SuperadminLoginView.as_view()),
    path('details/', SuperadminDetailAPI.as_view()),
]