from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
import requests
from .models import TMEmployeeDetail
from .serializers import EmployeeSerializers, UserWithEmployeeSerializer, EditEmployeeSerializers, EmployeeCreateSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated
from custom.permissions import IsOrganisation
from org.models import TMOrganisationDetail
from custom.models import User
from dept.models import OrgDepartment, OrgDesignation
from dept.serializers import OrgDepartmentSerializers, OrgDesignationSerializers
from custom.serializers import UserSerializer
from custom.utils import get_tokens_for_user
from rest_framework.parsers import MultiPartParser, FormParser




class OrgBasedEmpView(APIView):
    permission_classes = [IsOrganisation]
    def get(self, request):
        try:
            org_id=request.query_params.get("org_id")
            if not org_id:
                return Response({'status':"error", 'message':"Org id is required"}, status=status.HTTP_400_BAD_REQUEST)

            if not TMOrganisationDetail.objects.filter(id=org_id).exists():
                return Response({'status':"error", "message":"Organisation not found"}, status=status.HTTP_404_NOT_FOUND)
            
            data = User.objects.filter(org_id=org_id).exclude(emp_id__isnull=True)
            emp_ids = [emp.emp_id.id for emp in data]
            emp_data = TMEmployeeDetail.objects.filter(id__in = emp_ids)

            serializer = EmployeeSerializers(emp_data, many=True).data
            return Response({'status':"success", "data":serializer}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"status":"Error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)



class CreateEmployeeWithUserView(APIView):
    permission_classes = [IsOrganisation]
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request):
        print(f"request dat a:{request.data}")
        serializer = UserWithEmployeeSerializer(data=request.data)
        # print(f"serializer:{serializer}")
        if serializer.is_valid():
            user = serializer.save()
            return Response({"message": "Employee and User created", "user_id": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def get(self, request, id=None):
        try:
            if id:
                employee = get_object_or_404(TMEmployeeDetail, id=id)
                serializer = EmployeeSerializers(employee)
                return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
            else:
                employees = TMEmployeeDetail.objects.all()
                serializer = EmployeeSerializers(employees, many=True)
                return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": "Error", "message": str(e)}, status=status.HTTP_404_NOT_FOUND)
            

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
                serializer = EmployeeCreateSerializer(data, data=request.data)
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
                serializer = EmployeeCreateSerializer(data, data = request.data, partial = True)
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




class CheckEmpDuplicateFieldAPIView(APIView):
    permission_classes=[IsOrganisation]
    allowed_fields={
        'email':'email',
        'EmployeeId':'EmployeeId',
        'EmpMobNumber':'EmpMobNumber'
    }

    def get(self, request):
        item = request.query_params.get('item')
        value = request.query_params.get('value')
        emp_id = request.query_params.get('emp_id')

        if not item and not value:
            return Response({'status':"Error","message":"Both item and value field are required"})
        
        if item not in self.allowed_fields:
            return Response({"status":"error","message":"Invalid field"}, status=status.HTTP_400_BAD_REQUEST)
        
        if item == 'email':
            emp_email = User.objects.filter(email=value)
            if emp_id:
                exclude_id = emp_email.exclude(emp_id=emp_id)
            data_exists = exclude_id.exists()

        elif item == 'EmployeeId':
            emp_empcode = TMEmployeeDetail.objects.filter(EmployeeId = value)
            if emp_id:
                exclude_id = emp_empcode.exclude(id=emp_id)
            data_exists = exclude_id.exists()

        elif item =='EmpMobNumber':
            emp_mobnum = TMEmployeeDetail.objects.filter(EmpMobNumber=value)
            if emp_id:
                exclude_id = emp_mobnum.exclude(id=emp_id)
            data_exists = exclude_id.exists()
            
        return Response({'status':"success","data":data_exists}, status=status.HTTP_200_OK)



        