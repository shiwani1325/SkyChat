from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from .models import Superadmin
from custom.utils import get_tokens_for_user
from .serializers import SuperadminSerializers
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated
from custom.models import User
from custom.serializers import UserSerializer
from org.models import Organisation
from org.serializers import OrganisationSerializers
from custom.permissions import IsOrganisation, IsSuperAdmin


class Superadminview(APIView):
    permission_classes = [AllowAny]
    def get(self, request, id=None):
        try:
            if id:
                data = Superadmin.objects.get(id=id)
                serializer = SuperadminSerializers(data)
                return Response({"status":"success", "data":serializer.data}, status=status.HTTP_200_OK)

            else:
                data= Superadmin.objects.all()
                serializer =SuperadminSerializers(data, many=True)

                return Response({"status":"success", "data":serializer.data}, status=status.HTTP_200_OK)
        except Superadmin.DoesNotExist:
            return Response({"status":"Error", "message":"Super admin not found"}, status=status.HTTP_400_BAD_REQUEST)


    def post(self, request):
        try:
            role = request.data.get('role')

            if role not in ['superadmin', 'organisation','employee']:
                return Response({'error':"Invalid role"}, status=status.HTTP_400_BAD_REQUEST)

            userserializers = UserSerializer(data= request.data)

            if userserializers.is_valid():
                user= userserializers.save()
            else:
                return Response({'user_errors':userserializers.errors}, status=status.HTTP_400_BAD_REQUEST)

            serializer_data= SuperadminSerializers(data = request.data)
            if serializer_data.is_valid():
                serializer_data.save(user=user)
                return Response({"status":"success","data":serializer_data.data}, status=status.HTTP_201_CREATED)

            else:
                return Response({'errors': serializer_data.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'status':"error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, id =None):
        if id is None:
            return Response({"status":"Error","message":"Provide valid id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            data = Superadmin.objects.get(id=id)
            data.delete()
            return Response({"status":"success","message":"Particular data get deleted"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status":"Error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SuperadminLoginView(APIView):
    permission_classes = [AllowAny]
   
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, email=email, password=password)
        if user is None:
            return Response({'error': 'Invalid credentials'}, status=401)

        tokens = get_tokens_for_user(user, user.role)
        return Response({
            'tokens': tokens,
            'user': UserSerializer(user).data
        })


class SuperadminViewOrg(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    def get(self, request):
        try:
            data = Organisation.objects.all()
            serializer= OrganisationSerializers(data, many=True)
            return Response({"status":"Success","data":serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status':"error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)

