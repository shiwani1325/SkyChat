from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/superadmin/',include('superadmin.urls')),
    path('api/custom/',include('custom.urls')),
    # path('api/chat/', include('chat.urls')),
    path('api/employee/',include('employee.urls')),
    path('api/org/',include('org.urls')),
    path('api/dept/',include('dept.urls')),

]
if settings.DEBUG:
  urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)