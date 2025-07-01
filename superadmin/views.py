from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from custom.utils import get_tokens_for_user
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from custom.models import User
from custom.serializers import UserSerializer


class SuperadminLoginView(APIView):
    permission_classes = [AllowAny]
   
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response({'error': 'Invalid credentials'}, status=401)

        tokens = get_tokens_for_user(user, user.role.RoleName)
        return Response({
            'tokens': tokens,
            'user': UserSerializer(user).data
        })
