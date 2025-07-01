# def greet(name):
#     print(f"Hello {name}")

# greet("Shiwani")


# list_data = ["Apple","banana"]
# new_list = list_data + ["grapes"]
# print(new_list)

# dic_data = {
#     "name":"Shiwani",
#     "age":"24",
#     "add":"abc"
# }
# # print(dic_data["name"])
# value= input("Enter a key name:")

# final_value = dic_data.get(value)
# print(final_value)


# text="Python is fun"

# print(text[0:6])

# from datetime import datetime

# now_time= datetime.now()
# print(now_time.strftime("%Y-%m-%d %H-%M-%S"))

# import math

# num=5

# final_value=math.pi*(num**2)
# print(final_value)


# values=input("Enter value here:")
# separate_value=values.split(',')
# print(separate_value)
# type_value=tuple(separate_value)
# print(type_value)

# file_name="hello.py"
# ext = file_name.split('.')[-2]
# print(ext)







# num=10
# while num>=1:
#     print(num)
#     num=num-1




# import os
# import django

# # Setup Django environment
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")  # change 'mysite' to your project name
# django.setup()

# from employee.models import TMEmployeeDetail  # change 'your_app' to your app name
# from django.db.models import Count

# def find_duplicates():
#     duplicates = (
#         TMEmployeeDetail.objects
#         .values('EmpMobNumber')
#         .annotate(mob_count=Count('EmpMobNumber'))
#         .filter(mob_count__gt=1)
#     )

#     if duplicates:
#         print("Duplicate Mobile Numbers Found:\n")
#         for dup in duplicates:
#             print(f"Mobile Number: {dup['EmpMobNumber']} | Count: {dup['mob_count']}")
#     else:
#         print("No duplicates found. All mobile numbers are unique.")

# if __name__ == "__main__":
#     find_duplicates()




# n=int(input("enter any number:"))
# a= n*(n+1)//2
# print(a)



# n= "Hello!"
# print(n[-1:])



# import json

# input_data = '{"name": "Shiwani"}'
# data = json.loads(input_data)


# if 'name' in data:
#     name = data['name']
#     message = f"Hello, {name}! Welcome to the API!"
#     response = {'message': message}
# else:
#     response = {'error': 'Please provide a name'}

# print(json.dumps(response, indent=4))



# import json

# # In-memory task list
# tasks = []
# task_id_counter = 1

# # Simulate API requests
# def handle_request(method, input_json=None):
#     global task_id_counter, tasks

#     if method == 'POST':
#         data = json.loads(input_json)
#         if 'task' not in data:
#             response = {'error': 'Task description is required'}
#         else:
#             task = {
#                 'id': task_id_counter,
#                 'task': data['task']
#             }
#             tasks.append(task)
#             task_id_counter += 1
#             response = {'message': 'Task added successfully', 'task': task}

#     elif method == 'GET':
#         response = {'tasks': tasks}

#     elif method == 'DELETE':
#         data = json.loads(input_json)
#         task_id = data.get('id')
#         if not task_id:
#             response = {'error': 'Task id is required to delete'}
#         else:
#             original_length = len(tasks)
#             tasks = [t for t in tasks if t['id'] != task_id]
#             if len(tasks) < original_length:
#                 response = {'message': f'Task with id {task_id} deleted successfully'}
#             else:
#                 response = {'error': f'No task found with id {task_id}'}

#     else:
#         response = {'error': 'Unsupported HTTP method'}

#     print(json.dumps(response, indent=4))


# # ---------------------------
# # Simulating API calls below:
# # ---------------------------

# # 1️⃣ Add a task (POST)
# handle_request('POST', '{"task": "Buy groceries"}')
# # handle_request('POST', '{"task": "Finish Python project"}')

# # # 2️⃣ Get all tasks (GET)
# # handle_request('GET')

# # # 3️⃣ Delete a task (DELETE)
# # handle_request('DELETE', '{"id": 1}')

# # # 4️⃣ Get all tasks again to verify deletion
# # handle_request('GET')





# set1={10,True,1, False,0,0,1,'jenny',True,False}
# print(set1)