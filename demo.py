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