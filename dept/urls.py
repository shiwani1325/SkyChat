from django.urls import path
from .views import DepartmentView, DesignationView, DesignationListViewDept

urlpatterns= [
    path('deplist/',DepartmentView.as_view()),
    path('deplist/<int:id>',DepartmentView.as_view()),
    path('deslist/',DesignationView.as_view()),
    path('deslist/<int:id>',DesignationView.as_view()),
    path('des/list/',DesignationListViewDept.as_view()),
] 