from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import requests
from .models import TMEmployeeDetail
from .serializers import EmployeeSerializers, UserWithEmployeeSerializer, EditEmployeeSerializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from custom.permissions import IsOrganisation
from org.models import TMOrganisationDetail
from custom.models import User
from dept.models import OrgDepartment, OrgDesignation
from dept.serializers import OrgDepartmentSerializers, OrgDesignationSerializers
from custom.serializers import UserSerializer
from custom.utils import get_tokens_for_user


class CreateEmployeeWithUserView(APIView):
    permission_classes = [IsOrganisation]
    def post(self, request):
        serializer = UserWithEmployeeSerializer(data=request.data)
        # print(f"serializer:{serializer}")
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "Employee and User created", "user_id": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def get(self, request, id=None):
        try:
            if id:
                data = TMEmployeeDetail.objects.get(id=id)
                serializer = EmployeeSerializers(data)

            else:
                data = TMEmployeeDetail.objects.all()
                serializer = EmployeeSerializers(data, many=True)
            return Response({"status":"success","data":serializer.data}, status =status.HTTP_200_OK)
    
        except Exception as e:
            return Response({"status":"Error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)
            

    def delete(self, request, id=None):
        try:
            if id:
                data = TMEmployeeDetail.objects.get(id=id)
                serializer = EmployeeSerializers(data)
                if request.user.is_authenticated:
                    data.UpdatedBy = request.user

                if data.Status == 'inactive':
                    data.Status = 'active'
                else:
                    data.Status = 'inactive'

                data.save()
                updated_data = serializer.data
                return Response({'status':"success","message":"Particular employee data get inactive", "data":updated_data}, status=status.HTTP_200_OK)

        except TMEmployeeDetail.DoesNotExist:
            return Response({'status':"error", "message":"Employee not found with this ID"}, status=status.HTTP_404_NOT_FOUND)


    def put(self, request, id=None):
        try:
            if id:
                data = get_object_or_404(TMEmployeeDetail, id=id)
                serializer = EmployeeSerializers(data, data=request.data)
                if serializer.is_valid():
                    if request.user.is_authenticated:
                        data.UpdatedBy = request.user
                    serializer.save()
                return Response({'status':"success", "data":serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status":"error","message":str(e)}, status =status.HTTP_400_BAD_REQUEST)


    def patch(self,request, id=None):
        try:
            if id:
                data= get_object_or_404(TMEmployeeDetail, id=id)
                serializer = EmployeeSerializers(data, data = request.data, partial = True)
                if serializer.is_valid():
                    if request.user.is_authenticated:
                        data.UpdatedBy = request.user
                    serializer.save()
                return Response({'status':"success", "data":serializer.data}, status =status.HTTP_200_OK)
        except Exception as e:
            return Response({'status':"error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)



class EditEmployeeWithUserView(APIView):
    permission_classes = [IsOrganisation]
    def get(self, request, id=None):
        try:
            if id:
                data = TMEmployeeDetail.objects.get(id=id)
                serializer = EditEmployeeSerializers(data)
            else:
                data = TMEmployeeDetail.objects.all()
                serializer = EditEmployeeSerializers(data)
            return Response({'status':"success", "data":serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status':"error","message":str(e)}, status=status.HTTP_400_BAD_REQUEST)

