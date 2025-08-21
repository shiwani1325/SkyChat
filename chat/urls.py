from django.urls import path
from .views import chathistory, AudioVideoSendView

urlpatterns=[
    path('chathistory/', chathistory.as_view()),
    path('chathistory/<str:message_id>/', chathistory.as_view(), name='delete_message'),
    path('upload_video/', AudioVideoSendView.as_view(), name="sendvideoreceiver"),
]