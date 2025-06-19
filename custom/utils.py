from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

def get_tokens_for_user(user, role):
    refresh = RefreshToken.for_user(user)
    refresh['data'] = role
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }