from django.shortcuts import render
from .models import TMOrganisationDetail
from .serializers import OrganisationSerializer, UserWithOrganisationSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from custom.permissions import IsOrganisation
from rest_framework_simplejwt.authentication import JWTAuthentication
from custom.models import User
from custom.serializers import UserSerializer
from custom.utils import get_tokens_for_user
from rest_framework.parsers import MultiPartParser, FormParser

class CreateOrgWithUserView(APIView):
    permission_classes = [AllowAny, IsAdminUser]
    parser_classes=[MultiPartParser, FormParser]

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



class CheckOrgDuplicateFieldAPIView(APIView):
    permission_classes = [IsAdminUser]
    allowed_fields ={
        'email':'email',
        'OrgName':'OrgName',
        'OrgCode':'OrgCode',
        'OrgMobNum':'OrgMobNum',
        'OrgCodeName': 'OrgCodeName',
    }

    def get(self, request):
        item = request.query_params.get('item')
        value = request.query_params.get('value')
        org_id=request.query_params.get('org_id')
        org_name = request.query_params.get('OrgName')
        org_code = request.query_params.get('OrgCode')

        if not item and not value:
            return Response({'status':"error","message":"Both item and value field are required"})

        if item not in self.allowed_fields:
            return Response({'status':"error","message":"Invalid Field"},status=status.HTTP_400_BAD_REQUEST)

        if item =='email':
            org_email = User.objects.filter(email = value)
            if org_id :
                exclude_id = org_email.exclude(org_id=org_id)
            data_exists=exclude_id.exists()


        elif item == 'OrgMobNum':
            org_mobnum = TMOrganisationDetail.objects.filter(OrgMobNum= value)
            if org_id:
                exclude_id = org_mobnum.exclude(id = org_id)
            data_exists = exclude_id.exists()

        elif item =='OrgCodeName':
            if not org_name or not org_code:
                return Response({'status':"error","message":"Both orgname and orgcode are required"}, status =status.HTTP_400_BAD_REQUEST)

            org_data=TMOrganisationDetail.objects.filter(OrgName=org_name, OrgCode=org_code)
            if org_id:
                exclude_id=org_data.exclude(id=org_id)            
            data_exists = exclude_id.exists()
        
        return Response({'status':"success","data":data_exists}, status=status.HTTP_200_OK)




class OrgDetailAPI(APIView):
    permission_classes = [IsOrganisation]
    def get(self, request):
        try:
            id = request.query_params.get('id')
            if id:
                data = TMOrganisationDetail.objects.get(id=id)
                serializer = OrganisationSerializer(data)
                return Response({'status':"success", "data":serializer.data}, status=status.HTTP_200_OK)

            else:
                return Response({"status":"success",'message':"Provide valid id"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'status':"Error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)

        


        
