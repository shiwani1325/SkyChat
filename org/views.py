from django.shortcuts import render
from .models import Organisation
from .serializers import OrganisationSerializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from custom.models import User
from custom.serializers import UserSerializer
from custom.utils import get_tokens_for_user
from employee.serializers import EmployeeSerializers
from employee.models import Employee
from custom.permissions import IsOrganisation, IsSuperAdmin




class org_view(APIView):
    permission_classes = [AllowAny]
    def get(self, request, id=None):
        try:
            if id:
                data =  Organisation.objects.get(id=id)
                serializer = OrganisationSerializers(data)
                return Response({"status":"success", "data":serializer.data}, status=status.HTTP_200_OK)
            
            else:
                data= Organisation.objects.all()
                serializer = OrganisationSerializers(data, many=True)
                return Response({"status":"success",'data':serializer.data}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'status':"Error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request, id =None):
        try:
            role = request.data.get('role')
            if role not in ['organisation']:
                return Response({'error':'Invalid role'},status=status.HTTP_400_BAD_REQUEST )
            
            userserializers = UserSerializer(data=request.data)

            if userserializers.is_valid():
                user= userserializers.save()
            else:
                return Response({'status':"error", 'messsage': userserializers.errors}, status=status.HTTP_400_BAD_REQUEST)

            serializer_data = OrganisationSerializers(data=request.data)

            if serializer_data.is_valid():
                serializer_data.save(user=user)
                return Response({"status":"success","data":serializer_data.data}, status=status.HTTP_201_CREATED)
            # else:
            #     return Response({"status":"Error", "message":"Provide valid data"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"sttaus":"error", "message":str(e)}, status = status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id=None):
        if id is None:
            return Response({"status":"Error", "message":"Provide Id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data =  Organisation.objects.get(id=id)
            data.delete()
            return Response({"status":"success", "message":"data get deleted"}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'status':"Error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)



class Org_login(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get('email')
        password =request.data.get('password')
        user = authenticate(request, email=email, password=password)

        if user is None:
            return Response({"status":"Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        
        tokens = get_tokens_for_user(user, user.role)
        return Response({'tokens':tokens, 'user':UserSerializer(user).data}, status = status.HTTP_200_OK)



class OrgViewEmp(APIView):
    permission_classes = [IsAuthenticated, IsOrganisation]

    def get(self, request):
        try:
            emp_data = Employee.objects.all()
            serializer = EmployeeSerializers(emp_data, many=True)
            return Response({'status':"Success", "data":serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status':"error", 'message':str(e)}, status=status.HTTP_400_BAD_REQUEST)