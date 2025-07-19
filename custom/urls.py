from django.urls import path
from .views import AllLoginView,ViewUserData, RoleView

urlpatterns=[
    path('login/', AllLoginView.as_view()),
    path('user/',ViewUserData.as_view()),
    path('role/data/', RoleView.as_view()),
]