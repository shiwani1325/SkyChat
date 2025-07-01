from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny
from custom.permissions import IsOrganisation
from rest_framework.response import Response
from .models import OrgDepartment, OrgDesignation
from .serializers import OrgDepartmentSerializers, OrgDesignationSerializers


class DepartmentView(APIView):
    permission_classes=[IsOrganisation]
    def get(self, request,id=None):
        try:
            if id:
                data = OrgDepartment.objects.get(id=id)
                serializer = OrgDepartmentSerializers(data)
            else:
                data = OrgDepartment.objects.all()
                serializer = OrgDepartmentSerializers(data, many=True)
            
            return Response({'status':"success", "data":serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status':"error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)




class DesignationView(APIView):
    permission_classes = [IsOrganisation]

    def get(self, request, id=None):
        try:
            if id:
                data = OrgDesignation.objects.get(id=id)
                serializer = OrgDesignationSerializers(data)
            else:
                data = OrgDesignation.objects.all()
                serializer = OrgDesignationSerializers(data, many=True)
            
            return Response({'status':"success", "data":serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'status':'error',"message":str(e)}, status=status.HTTP_400_BAD_REQUEST)



class DesignationListViewDept(APIView):
    permission_classes = [IsOrganisation]

    def get(self, request, id=None):
        try:
            dep_id = request.query_params.get('dept_id')
            data = OrgDesignation.objects.filter(DepId=dep_id)
            serializer = OrgDesignationSerializers(data, many=True)
            return Response({'status':"success","data":serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'status':"error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)



