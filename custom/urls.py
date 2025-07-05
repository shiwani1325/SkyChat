from django.urls import path
from .views import AllLoginView,ViewUserData

urlpatterns=[
    path('login/', AllLoginView.as_view()),
    path('user/',ViewUserData.as_view()),
]