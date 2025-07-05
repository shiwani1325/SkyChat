# keys = ["a","b","c","d"]
# values = [1,1,2,1]
# a={}
# i=0
# while i<len(keys):
#     a[keys[i]] = values[i]
#     i=i+1
# print(a)

keys = ["a","b","c","d"]
values = [1,4,2,8,90,100]

# final = {}
# for i in range(len(keys)):
#     print(f"i value is :{i}")
#     final[keys[i]] = values[i]
#     print(f"finalL{final}")
#     i = i+1


count=0
start=0
# for i in range(len(values)):
#     if values[i]>3:
#         count+=1
# print(count)



while start < len(values):
    if values[start] >3:
        count+=1
        start+=1
    else:
        start+=1
print(count)