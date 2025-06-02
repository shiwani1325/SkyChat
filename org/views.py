from django.shortcuts import render
from .models import Organisation
from .serializers import OrganisationSerializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication



class org_view(APIView):
    def get(self, request, id=None):
        if id is None:
            return Response({"status":"Error", "message":"Provide Id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data =  Organisation.objects.get(id=id)
            serializer = OrganisationSerializers(data)
            return Response({"status":"success", "data":serializer.data}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({'status':"Error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request, id =None):
        try:
            serializer_data = OrganisationSerializers(request=request.data)
            if serializer_data.is_valid():
                serializer_data.save()
                return Response({"status":"success","data":serializer_data.data}, status=status.HTTP_201_CREATED)
            else:
                return Response({"status":"Error", "message":"Provide valid data"}, status=status.HTTP_400_BAD_REQUEST)
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
        password = request.data.get('password')
        if not email or not password:
            return Response({"status":"Error", "message":"Email and password are required"}, sttaus=status.HTTP_400_BAD_REQUEST)

        try:
            org_detail = Organisation.objects.get(OrgEmail=email)
        except Organisation.DoesNotExist:
            return Response({"status":"Error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        if password != org_detail.password:
            return Response({"status":"Error", "message":"Provide valid password"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = OrganisationSerializers(org_detail)
        return Response({"status":"Success", "data":serializer.data,"message":"Login Successful"}, status=status.HTTP_200_OK)


