# Generated by Django 3.2.9 on 2021-12-20 01:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0004_auto_20211220_0917'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='task_description',
            field=models.CharField(max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='task_status',
            field=models.IntegerField(default=0),
        ),
    ]
