from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import EmployeeList, EmployeeLogin

urlpatterns=[
    path('employeelist/',EmployeeList.as_view()),
    path('employeelist/<int:id>',EmployeeList.as_view()),
    path('emplogin/', EmployeeLogin.as_view()),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)