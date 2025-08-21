from django.urls import path
from .views import GroupChatRoomView, EmployeeListOrgBasedView

urlpatterns=[
    path('create/', GroupChatRoomView.as_view()),
    path('group/data/<int:id>/', GroupChatRoomView.as_view()),
    path('group/data/', GroupChatRoomView.as_view()),
    path('org/emp_list/',EmployeeListOrgBasedView.as_view()),
]