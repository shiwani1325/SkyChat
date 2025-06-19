from django.db import models

class OrgDepartment(models.Model):
    DeptName = models.CharField(max_length=50) 

    class Meta:
        db_table = 'OrgDepartment'

    def __str__(self):
        return self.DeptName

class OrgDesignation(models.Model):
    DepId = models.ForeignKey(OrgDepartment, on_delete=models.CASCADE)
    DesName = models.CharField(max_length=100) 
    class Meta:
        db_table = 'OrgDesignation'


    def __str__(self):
        return f'{self.DepId} and {self.DesName}'
