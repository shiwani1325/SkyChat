from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import requests
from .models import Employee
from .serializers import EmployeeSerializers
from rest_framework.permissions import AllowAny
from org.models import Organisation
from custom.serializers import UserSerializer
from custom.utils import get_tokens_for_user



class EmployeeList(APIView):
    def get(self, request, id=None):
        try:
            if id:
                data = Employee.objects.get(id=id)
                serializer = EmployeeSerializers(data)
                return Response({"status":"success", "data":serializer.data}, status=status.HTTP_200_OK)
            else:
                data = Employee.objects.all()
                serializer = EmployeeSerializers(data, many=True)
                return Response({"status":"success","data":serializer.data}, status =status.HTTP_200_OK)
      
        except Exception as e:
            return Response({"status":"Error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        try:
            role = request.data.get('role')
            if role not in ['employee']:
                return Response({'status':'error', 'message':"Invalid role"}, status = status.HTTP_400_BAD_REQUEST)

            userserializers = UserSerializer(data = request.data)
            if userserializers.is_valid():
                user = userserializers.save()
            else:
                return Response({'user_errors':userserializers.errors}, status=status.HTTP_400_BAD_REQUEST)

            serializer_data = EmployeeSerializers(data = request.data)
            # print(f'serializer data :{serializer_data}')
            if serializer_data.is_valid():
                serializer_data.save(user=user)
                return Response({'status':'success', 'data':serializer_data.data}, status=status.HTTP_200_OK)

            return Response({'status':"success", 'data':serializer_data.errors}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'status':'error','message':str(e)}, status=status.HTTP_400_BAD_REQUEST)


        


class EmployeeLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"status": "Error", "message": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response({'error': 'Invalid credentials'}, status=401)

        tokens = get_tokens_for_user(user, user.role)
        try:
            data = Employee.objects.get(user=user)
            serializer=EmployeeSerializers(data)
            employee_data=serializer.data
        except Employee.DoesNotExist:
            return Response({"status":"error", 'message':"Employee not found"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'tokens': tokens,
            # 'user': UserSerializer(user).data,
            'employee':employee_data
        })




