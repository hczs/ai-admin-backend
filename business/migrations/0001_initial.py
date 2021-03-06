# Generated by Django 3.2.9 on 2021-12-16 07:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, help_text='创建时间', verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, help_text='修改时间', verbose_name='修改时间')),
                ('file_name', models.CharField(max_length=50)),
                ('file_size', models.BigIntegerField()),
                ('file_path', models.CharField(max_length=100)),
                ('extract_path', models.CharField(max_length=100)),
            ],
            options={
                'verbose_name': '文件',
                'verbose_name_plural': '文件',
                'db_table': 'tb_file',
            },
        ),
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(default=django.utils.timezone.now, help_text='创建时间', verbose_name='创建时间')),
                ('update_time', models.DateTimeField(auto_now=True, help_text='修改时间', verbose_name='修改时间')),
                ('task_name', models.CharField(max_length=50)),
                ('task_description', models.CharField(max_length=150)),
                ('task_status', models.IntegerField()),
                ('task', models.CharField(max_length=30)),
                ('model', models.CharField(max_length=30)),
                ('dataset', models.CharField(max_length=30)),
                ('config_file', models.CharField(max_length=100)),
                ('saved_model', models.BooleanField(default=True)),
                ('train', models.BooleanField(default=True)),
                ('batch_size', models.BigIntegerField()),
                ('train_rate', models.FloatField()),
                ('eval_rate', models.FloatField()),
                ('max_epoch', models.IntegerField()),
                ('gpu', models.BooleanField(default=True)),
                ('gpu_id', models.IntegerField()),
                ('creator', models.ForeignKey(db_constraint=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('data_file', models.ForeignKey(db_constraint=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to='business.file')),
            ],
            options={
                'verbose_name': '任务',
                'verbose_name_plural': '任务',
                'db_table': 'tb_task',
            },
        ),
    ]
