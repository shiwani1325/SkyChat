from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async  
import json
from .models import Employee
from .serializers import EmployeeSerializers


class EmployeeList(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        request_data = json.loads(text_data)
        employee_id = request_data.get('employee_mail')
        
        try:
            employee = await self.get_employee(employee_id)
            org_id, org_name = await self.get_org_details(employee)

            serializer = EmployeeSerializers(employee)
            employee_data = serializer.data

            other_employees = await self.get_other_employee(org_id, employee.id)
            employees_list = await self.prepare_employee_list(other_employees, org_name)

            await self.send(text_data=json.dumps({
                "Status": "Success",
                "Data": employee_data,
                "message": "Login Successful",
                "Org_Employees": {
                    "count_type": "unread_count",
                    "chat_receiver": employee.employee_id,
                    "count": 0,
                    "unread_sender_count": 0,
                    "unread_messages": [],
                    "employee_list": employees_list
                }
            }))

        except Employee.DoesNotExist:
            await self.send(text_data=json.dumps({
                "Status": "Error",
                "message": "Employee not found"
            }))

    @database_sync_to_async
    def get_employee(self, employee_mail):
        return Employee.objects.get(email=employee_mail)

    @database_sync_to_async
    def get_other_employee(self, org_id, excluded_emp_id):
        return list(Employee.objects.filter(Org_id=org_id).exclude(id=excluded_emp_id))

    @sync_to_async
    def serialize_employee(self, employee):
        return EmployeeSerializers(employee).data

    @sync_to_async
    def prepare_employee_list(self, employees, org_name):
        return [
            {
                "employee_id": emp.employee_id,
                "employee_data": {
                    "name": emp.name,
                    "image": emp.image.url if emp.image else None,
                    "email": emp.email,
                    "status": emp.status,
                    "company": org_name,
                },
                "id": None,
                "latest_message": None,
                "unread_notifications": {
                    "sender": [],
                    "receiver_employee_id": [],
                    "total_unread_count": 0,
                    "unread_messages": []
                }
            }
            for emp in employees
        ]
    
    @sync_to_async
    def get_org_details(self, employee):
        org = employee.Org_id
        return org.id, org.OrgName
