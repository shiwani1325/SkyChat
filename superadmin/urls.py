from django.urls import path
from .views import SuperadminLoginView

urlpatterns=[
    path('login_sa/', SuperadminLoginView.as_view()),
]