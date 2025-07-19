from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .utils import get_tokens_for_user
from django.contrib.auth import authenticate
from .serializers import UserSerializer, RoleSerializers
from .models import User, TMRole
from org.models import TMOrganisationDetail
from employee.models import TMEmployeeDetail
from org.serializers import OrganisationSerializer, UserWithOrganisationSerializer
from employee.serializers import EmployeeSerializers, UserWithEmployeeSerializer


class AllLoginView(APIView):
    permission_classes = [AllowAny]
 
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if email:
            email = email.lower()

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
                
                if serializer_data['Status']=='Active':
                    user_final_data={**serializer_data, **user_data }
                
                    return Response({"status":"success",'tokens': tokens, "user":user_final_data}, status=status.HTTP_200_OK)
                return Response({'status':"error", "message":"Your account is currently Inactive"}, status=status.HTTP_403_FORBIDDEN)

            except TMOrganisationDetail.DoesNotExist:
                return Response({"status":"error", "message":"Organisation data not found"}, status=status.HTTP_400_BAD_REQUEST)
            
        elif role_id == Role_user:
            try:
                serializer_data=self.employee_view(user)
                if serializer_data['Status'] == 'Active':
                    user_final_data={**serializer_data, **user_data }
                    orgid = user_final_data['org_id']
                    serializer_data = self.organisation_status(orgid)
                    
                    if serializer_data['Status'] == 'inactive':
                        return Response({'status':"error", "message":"Your account is currently Inactive"}, status=status.HTTP_403_FORBIDDEN)
                    return Response({'status':"success",'tokens': tokens, "user":user_final_data}, status=status.HTTP_200_OK)
                return Response({'status':"error", "message":"Your account is currently Inactive"}, status=status.HTTP_403_FORBIDDEN)
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

    def organisation_status(self, id):
        org_data = TMOrganisationDetail.objects.get(id=id)
        serializer = OrganisationSerializer(org_data)
        return serializer.data



class ViewUserData(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        data = User.objects.all()
        serializer_data = UserSerializer(data, many=True)

        return Response({'status':"Success","data":serializer_data.data}, status=status.HTTP_200_OK)





class RoleView(APIView):
    permission_classes = [ IsAuthenticated,IsAdminUser]
    def get(self, request):
        data=TMRole.objects.all()
        serializer = RoleSerializers(data, many=True)
        return Response({'status':"success","data":serializer.data}, status=status.HTTP_200_OK)
    

    def post(self,request):
        
        serializer = RoleSerializers(data= request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                return Response({'status':"success", "data":serializer.data, "message":"Role added"}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'status':"error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({'status':"error", "message":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


