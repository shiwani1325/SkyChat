from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from custom.utils import get_tokens_for_user
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
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



class SuperadminDetailAPI(APIView):
    permission_classes=[IsAdminUser]
    def get(self, request):
        try:
            id = request.query_params.get('id')
            if id:
                data = User.objects.get(id=id)
                print(f"data :{data}")
                serializer =  UserSerializer(data).data
                return Response({'status':"success", "data":serializer})
            else:
                return Response({'status':"error", "message":"Provide valid id"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status':"error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)
