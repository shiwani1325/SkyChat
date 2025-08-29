from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from custom.permissions import IsEmployee
from .models import EmployeeGroup
from .serializers import EmployeeGroupSerializer, EmployeeListSerializerGroup
from employee.models import TMEmployeeDetail
from custom.models import User


# API to create group
class CreateEmployeeGroupAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def post(self, request):
        serializer = EmployeeGroupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# API to get employees by org id
class EmployeeListByOrgAPIView(APIView):
    permission_classes = [IsAuthenticated, IsEmployee]

    def get(self, request, org_id):
        employees = User.objects.filter(org_id=org_id).exclude(emp_id__isnull=True)
        print(f"employees:{employees}")
        emp_ids = [emp.emp_id.id for emp in employees]
        print(f"empl_id :{emp_ids}")
        emp_data = TMEmployeeDetail.objects.filter(id__in = emp_ids, Status='Active')
        print(f"emp_data :{emp_data}")
        serializer = EmployeeListSerializerGroup(emp_data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)









# from django.shortcuts import render
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.permissions import AllowAny
# from django.conf import settings
# from .models import EmployeeGroup, EmployeeGroupChat
# from .serializers import EmployeeGroupSerializers, EmployeeGroupSerializersDetails, EmployeeListSerializerGroup
# from org.models import TMOrganisationDetail
# from custom.models import User
# from employee.models import TMEmployeeDetail
# from employee.serializers import EmployeeSerializers 
# # from .serializers import EmployeeSerializerGroup

# class GroupChatRoomView(APIView):
#     permission_classes=[AllowAny]

#     def post(self, request):
#         serializer = EmployeeGroupSerializers(data=request.data)
#         if serializer.is_valid():
#             try:
#                 user = serializer.save()
#                 return Response({'status':"success", "message":"Group is created successfully","data":serializer.data}, status=status.HTTP_201_CREATED)
#             except Exception as e:
#                 return Response({'status':"error", "message":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#         return Response({'status':"error", "message":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


#     def get(self, request, id=None):
#         try:
#             if not id:
#                 data =  EmployeeGroup.objects.all()
#                 # serializer = EmployeeGroupSerializers(data, many=True) # EmployeeGroupSerializersDetails
#                 serializer = EmployeeGroupSerializersDetails(data, many=True)
#                 return Response({'status':"success", "data":serializer.data}, status=status.HTTP_200_OK)
#             else:
#                 data=EmployeeGroup.objects.get(id=id)
#                 serializer = EmployeeGroupSerializersDetails(data)
#                 return Response({'status':"success", "data":serializer.data}, status=status.HTTP_200_OK)

#         except Exception as e:
#             return Response({'status':"error", "message":str(e)}, status=status.HTTP_400_BAD_REQUEST)

# class EmployeeListOrgBasedView(APIView):
#     permission_classes =[AllowAny]

#     def get(self, request):
#         try:
#             org_id = request.query_params.get('org_id')
#             if not org_id:
#                 return Response({'status':"error", "message":"Org id is required"}, status=status.HTTP_400_BAD_REQUEST)

#             if not TMOrganisationDetail.objects.filter(id=org_id).exists():
#                 return Response({'status':"error", "message":"Organisation not found"}, status=status.HTTP_404_NOT_FOUND)

#             data = User.objects.filter(org_id=org_id).exclude(emp_id__isnull=True)
#             emp_ids = [emp.emp_id.id for emp in data]
#             emp_data = TMEmployeeDetail.objects.filter(id__in = emp_ids, Status='Active')
#             serializer = EmployeeListSerializerGroup(emp_data, many=True)

#             return Response({'status':"success", "data":serializer.data}, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({'status':"error", "message":str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


