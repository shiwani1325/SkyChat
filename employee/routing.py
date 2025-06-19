# routing.py

from django.urls import re_path
# from .consumers import EmployeeList
# from chat.consumers import EmployeeChat
# from .consumers1 import EmployeeList1

websocket_urlpatterns = [
    # re_path(r'ws/employee_list/$',EmployeeList.as_asgi()),
    # re_path(r'ws/employee/$', EmployeeList1.as_asgi()),
    # # re_path(r'ws/notify/$',EmployeeList.as_asgi()),
    # re_path(r'ws/chat/(?P<sender_id>\w+)/(?P<receiver_id>\w+)/$', EmployeeChat.as_asgi()),
]
