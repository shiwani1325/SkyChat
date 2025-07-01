from django.urls import path
from .views import AllLoginView

urlpatterns=[
    path('login/', AllLoginView.as_view()),
]