from django.urls import path
from .views import CreateEmployeeGroupAPIView, EmployeeListByOrgAPIView
# from .views import GroupChatRoomView, EmployeeListOrgBasedView

urlpatterns=[
    path("groups/create/", CreateEmployeeGroupAPIView.as_view(), name="create_group"),
    path("employees/<int:org_id>/", EmployeeListByOrgAPIView.as_view(), name="employees_by_org"),
    # path('create/', GroupChatRoomView.as_view()),
    # path('group/data/<int:id>/', GroupChatRoomView.as_view()),
    # path('group/data/', GroupChatRoomView.as_view()),
    # path('org/emp_list/',EmployeeListOrgBasedView.as_view()),
]