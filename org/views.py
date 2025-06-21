from django.shortcuts import render
from .models import TMOrganisationDetail
from .serializers import OrganisationSerializer, UserWithOrganisationSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from custom.models import User
from custom.serializers import UserSerializer
from custom.utils import get_tokens_for_user


class CreateOrgWithUserView(APIView):
    permission_classes = [AllowAny, IsAdminUser]
    def post(self, request):
        serializer = UserWithOrganisationSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                return Response({"status":"Success","message": "Organisation and User created", "user_id": serializer.data}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"status":"error", "message":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=400)


    def get(self, request, id=None):
        try:
            if id:
                data =  TMOrganisationDetail.objects.get(id=id)
                serializer = OrganisationSerializer(data)
                return Response({"status":"success", "data":serializer.data}, status=status.HTTP_200_OK)
            
            else:
                data= TMOrganisationDetail.objects.all()
                serializer = OrganisationSerializer(data, many=True)
                return Response({"status":"success",'data':serializer.data}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'status':"Error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request,id=None):
        try:
            if id:
                data = TMOrganisationDetail.objects.get(id=id)
                if request.user.is_authenticated:
                    data.UpdatedBy=request.user

                if data.Status == 'inactive':
                    data.Status = 'active'
                else:
                    data.Status = 'inactive'
                
                data.save()
                return Response({"status":"success","message":"Particular org data get deleted"}, status=status.HTTP_200_OK)
               
        except TMOrganisationDetail.DoesNotExist:
            return Response({'status':"error", "message":"Organisation not found with this Id"}, status=status.HTTP_404_NOT_FOUND)

    
    def put(self, request, id=None):
        try:
            if id:
                data = TMOrganisationDetail.objects.get(id=id)
                serializer = OrganisationSerializer(data, data= request.data)
                if serializer.is_valid():
                    if request.user.is_authenticated:
                        data.UpdatedBy = request.user
                    serializer.save()

                return Response({'status':"success","data":serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status':"error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def patch(self, request, id=None):
        try:
            if id:
                data = TMOrganisationDetail.objects.get(id=id)
                serializer = OrganisationSerializer(data, data=request.data, partial=True)
                if serializer.is_valid():
                    if request.user.is_authenticated:
                        data.UpdatedBy = request.user
                    serializer.save()
                return Response({'status':"success","data":serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status':"error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)





# class CheckOrgDuplicateFieldAPIView(APIView):
#     permission_classes = [AllowAny]
#     allowed_fields ={
#         'email':'email',
#         'OrgName':'OrgName',
#         'OrgCode':'OrgCode',
#         'OrgMobNum':'OrgMobNum',
#     }

#     def get(self, request):
