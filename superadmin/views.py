from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from .models import Superadmin
from .serializers import SuperadminSerializers


class Superadminview(APIView):
    def get(self, request, id=None):
        if id:
            data = Superadmin.objects.get(id=id)
            serializer = SuperadminSerializers(data)
            return Response({"status":"success", "data":serializer.data}, status=status.HTTP_200_OK)

        else:
            return Response({"status":"Error", "Message":"Provide ID"}, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request):
        serializer_data= SuperadminSerializers(data = request.data)
        if serializer_data.is_valid():
            serializer_data.save()
            return Response({"status":"success","data":serializer_data.data}, status=status.HTTP_201_CREATED)


    def delete(self, request, id =None):
        if id is None:
            return Response({"status":"Error","message":"Provide valid id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = Superadmin.objects.get(id=id)
            data.delete()
            return Response({"status":"success","message":"Particular data get deleted"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status":"Error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SuperadminLoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'status': 'error', 'message': 'Email and password required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Superadmin.objects.get(email=email)

            if check_password(password, user.password):  # Assuming password is hashed
                refresh = RefreshToken.for_user(user)
                return Response({
                    'status': 'success',
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            else:
                return Response({'status': 'error', 'message': 'Invalid password'}, status=status.HTTP_401_UNAUTHORIZED)

        except Superadmin.DoesNotExist:
            return Response({'status': 'error', 'message': 'Superadmin not found'}, status=status.HTTP_404_NOT_FOUND)
