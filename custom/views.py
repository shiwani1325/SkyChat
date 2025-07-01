from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .utils import get_tokens_for_user
from django.contrib.auth import authenticate
from .serializers import UserSerializer
from .models import User
from org.models import TMOrganisationDetail
from employee.models import TMEmployeeDetail
from org.serializers import OrganisationSerializer, UserWithOrganisationSerializer
from employee.serializers import EmployeeSerializers, UserWithEmployeeSerializer


class AllLoginView(APIView):
    permission_classes = [AllowAny]
 
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        Role_superadmin=1
        Role_admin=2
        Role_user=3

        if not email or not password:
            return Response({"status":"error", "message":"Email and Password are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
        
        except User.DoesNotExist:
            return Response({'status':"error","message":"Invalid email"}, status=status.HTTP_401_UNAUTHORIZED)
        user = authenticate(request, email=email, password=password)
        

        if user is None:
            return Response({'status':'error', "message":"Invalid password"}, status=status.HTTP_401_UNAUTHORIZED)
            
        
        user_data=UserSerializer(user).data
        tokens = get_tokens_for_user(user, user_data)
        role_id = user_data['role']

        if role_id == Role_superadmin:
            return Response({
                'tokens': tokens,
                'user': user_data
            })

        elif role_id == Role_admin:
            try:
                serializer_data = self.organisation_view(user)

            except TMOrganisationDetail.DoesNotExist:
                return Response({"status":"error", "message":"Organisation data not found"}, status=status.HTTP_400_BAD_REQUEST)
            
        elif role_id == Role_user:
            try:
                serializer_data=self.employee_view(user)

            except TMEmployeeDetail.DoesNotExist:
                return Response({'status':"error", "message":"Employee data not found"}, status = status.HTTP_400_BAD_REQUEST)
        
        else:
            return Response({'status':"error", "message":"No user found"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_final_data = serializer_data | user_data

        return Response({
            'tokens': tokens,
            "user":user_final_data
        })
     
    def employee_view(self, user):
        emp_data = TMEmployeeDetail.objects.get(user=user)
        serializer = EmployeeSerializers(emp_data)
        return serializer.data

    def organisation_view(self, user):
        org_data = TMOrganisationDetail.objects.get(user=user)
        serializer = OrganisationSerializer(org_data)
        return serializer.data

  

