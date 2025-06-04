from django.urls import path
from .views import Superadminview, SuperadminLoginView, SuperadminViewOrg

urlpatterns=[
    path("s_admin/", Superadminview.as_view(), name="superadmin"),
    path("s_admin/<int:id>", Superadminview.as_view(), name="super_admin"),
    path('login_sa/', SuperadminLoginView.as_view()),
    path('saorg/',SuperadminViewOrg.as_view()),

]