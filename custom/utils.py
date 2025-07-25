from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

def get_tokens_for_user(user, user_data,user_final_data=None):
    refresh = RefreshToken.for_user(user)
    for key, value in user_data.items():
        refresh[key] = value
    # refresh['data'] = role
    # refresh['role_name'] = role.get('role_name')


    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }