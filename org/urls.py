from django.urls import path
from .views import CreateOrgWithUserView, CheckOrgDuplicateFieldAPIView, OrgDetailAPI

urlpatterns=[
    path('register/', CreateOrgWithUserView.as_view()),
    path('org/<int:id>', CreateOrgWithUserView.as_view()),
    path('org/', CreateOrgWithUserView.as_view()),
    path('org/exists/',CheckOrgDuplicateFieldAPIView.as_view()),
    path('details/', OrgDetailAPI.as_view()),
]