from django.urls import path
from .views import EmployeeList, EmployeeLogin

urlpatterns=[
    path('employeelist/',EmployeeList.as_view()),
    path('emplogin/', EmployeeLogin.as_view()),

]