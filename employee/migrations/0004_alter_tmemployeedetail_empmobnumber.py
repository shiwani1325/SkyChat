# Generated by Django 5.2.1 on 2025-06-18 11:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('employee', '0003_alter_tmemployeedetail_empmobnumber'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tmemployeedetail',
            name='EmpMobNumber',
            field=models.CharField(max_length=20, unique=True),
        ),
    ]
