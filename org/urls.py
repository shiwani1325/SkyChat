from django.urls import path
from .views import org_view, Org_login

urlpatterns=[
    path('company/', org_view.as_view()),
    path('company/<int:id>', org_view.as_view()),
    path('login/', Org_login.as_view()),
]