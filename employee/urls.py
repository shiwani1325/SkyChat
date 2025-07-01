from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import CreateEmployeeWithUserView, EditEmployeeWithUserView, CheckEmpDuplicateFieldAPIView

urlpatterns=[
    path('register/', CreateEmployeeWithUserView.as_view()),
    path('employeelist/',CreateEmployeeWithUserView.as_view()),
    path('employeelist/<int:id>',CreateEmployeeWithUserView.as_view()),
    path('edit/emp/<int:id>', EditEmployeeWithUserView.as_view()),
    path('emp/exists/',CheckEmpDuplicateFieldAPIView.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)