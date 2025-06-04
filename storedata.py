import os
import django
import urllib.request
from django.core.files.base import ContentFile
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

import requests
from employee.models import Employee
from org.models import Organisation
from custom.models import User

url = "http://127.0.0.1:8081/api/erpchat/employeelist/"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    employees = data.get("latest_employee_chats", [])
    org_map = {org.OrgCode: org for org in Organisation.objects.select_related("user").all() if org.OrgCode}

    for emp in employees:
        emp_id = emp.get("employee_id")
        emp_info = emp.get("employee_data", {})

        if not emp_id or not emp_info:
            print(f"⛔ Skipped: Missing employee_id or data")
            continue

        prefix = ''.join(filter(str.isalpha, emp_id))
        matched_org = org_map.get(prefix)

        if matched_org:
            try:
                email = emp_info.get("email")
                user, created_user = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "name": emp_info.get("name"),
                        "role": "employee",
                        "is_active": True
                    }
                )
                if created_user:
                    user.set_password("default123")
                    user.save()

                employee, created_emp = Employee.objects.get_or_create(
                    employee_id=emp_id,
                    defaults={
                        "user": user,
                        "organisation": matched_org.user,
                        "status": emp_info.get("status"),
                        "date_of_joining": timezone.now().date()
                    }
                )

                image_url = emp_info.get("image")
                if created_emp and image_url:
                    try:
                        result = urllib.request.urlopen(image_url)
                        employee.image.save(
                            f"{emp_id}.jpg",
                            ContentFile(result.read())
                        )
                        employee.save()
                    except Exception as img_err:
                        print(f"⚠️ Failed to download image for {emp_id}: {img_err}")

                if created_emp:
                    print(f"✅ Created: {user.name} ({emp_id})")
                else:
                    print(f"ℹ️ Already exists: {emp_id}")

            except Exception as e:
                print(f"❌ Error creating employee {emp_id}: {e}")
        else:
            print(f"⛔ No Organisation found with prefix '{prefix}' for {emp_id}")

else:
    print(f"❌ API failed: Status Code {response.status_code}")
