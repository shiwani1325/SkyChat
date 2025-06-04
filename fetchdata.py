
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

import requests
from employee.models import Employee
from org.models import Organisation
from django.utils import timezone

url = "http://127.0.0.1:8081/api/erpchat/employeelist/"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    employees = data.get("latest_employee_chats", [])
    org_map = {org.OrgCode: org for org in Organisation.objects.all() if org.OrgCode}

    for emp in employees:
        emp_id = emp.get("employee_id")
        emp_info = emp.get("employee_data", {})

        if not emp_id or not emp_info:
            print(f"⛔ Skipped due to missing employee_id or employee_data")
            continue
            
        prefix = ''.join(filter(str.isalpha, emp_id))
        matched_org = org_map.get(prefix)

        if matched_org:
            try:
                image_url = emp_info.get("image")
                employee, created = Employee.objects.get_or_create(
                    employee_id=emp_id,
                    defaults={
                        "Org_id": matched_org,
                        "name": emp_info.get("name"),
                        "email": emp_info.get("email"),
                        "status": emp_info.get("status"),
                        "password": "default123", 
                        "Date_of_joning": timezone.now().date()
                    }
                )
                if created and image_url:
                    try:
                        result = urllib.request.urlopen(image_url)
                        employee.image.save(
                            f"{emp_id}.jpg",
                            ContentFile(result.read())
                        )
                        employee.save()
                    except Exception as img_err:
                        print(f"⚠️ Failed to download image for {emp_id}: {img_err}")



                if created:
                    print(f"✅ Created: {employee.name} ({employee.employee_id})")
                else:
                    print(f"ℹ️ Already exists: {employee.employee_id}")
            except Exception as e:
                print(f"❌ Error for {emp_id}: {e}")
        else:
            print(f"⛔ OrgCode '{prefix}' not found for employee_id '{emp_id}'")

else:
    print(f"❌ API call failed with status code: {response.status_code}")
