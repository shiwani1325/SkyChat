from django.urls import path
from .views import CreateOrgWithUserView

urlpatterns=[
    path('register/', CreateOrgWithUserView.as_view()),
    path('org/<int:id>', CreateOrgWithUserView.as_view()),
    path('org/', CreateOrgWithUserView.as_view()),
]