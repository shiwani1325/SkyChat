from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from .models import Employee
from .serializers import EmployeeSerializers
from rest_framework.permissions import AllowAny
from org.models import Organisation


class EmployeeList(APIView):
    def get(self, request):
        data =  Employee.objects.all()
        serializer = EmployeeSerializers(data, many=True)

        return Response({"Status":"Success", "Data":serializer.data}, status=status.HTTP_200_OK)

        


class EmployeeLogin(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"status": "Error", "message": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            employee = Employee.objects.get(email=email)
        except Employee.DoesNotExist:
            return Response({"status": "Error", "message": "Invalid email"}, status=status.HTTP_400_BAD_REQUEST)
            
        if password != employee.password:
            return Response({"status": "Error", "message": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = EmployeeSerializers(employee)
        data = serializer.data
        org_id = data.get('Org_id')

        try:
            org = Organisation.objects.get(id=org_id)
            org_name = org.OrgName
        except Organisation.DoesNotExist:
            org_name = "Unknown company name"

        final_data = {
            "employee": data,
            "org_name": org_name
        }

        return Response({"status": "Success", "data": final_data, "message": "Login Successful"}, status=status.HTTP_200_OK)