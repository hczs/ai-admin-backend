from django.db import models

# Create your models here.
from authentication.models import Account
from common.models import BaseModel


class File(BaseModel):
    file_name = models.CharField(max_length=50, null=True)
    file_size = models.BigIntegerField(null=True)
    file_path = models.CharField(max_length=100, null=True)
    extract_path = models.CharField(max_length=100, null=True)

    class Meta:
        verbose_name = '文件'
        verbose_name_plural = verbose_name
        db_table = 'tb_file'

    def __str__(self):
        return self.file_name


class Task(BaseModel):
    task_name = models.CharField(max_length=50, unique=True)
    task_description = models.CharField(max_length=150, null=True)
    creator = models.ForeignKey(Account, null=True, db_constraint=False, on_delete=models.SET_NULL)
    data_file = models.ForeignKey(File, null=True, db_constraint=False, on_delete=models.SET_NULL)
    task_status = models.IntegerField(default=0)
    # 以下是任务执行参数
    task = models.CharField(max_length=30)
    model = models.CharField(max_length=30)
    dataset = models.CharField(max_length=30)
    config_file = models.CharField(max_length=100, null=True)
    saved_model = models.BooleanField(null=True)
    train = models.BooleanField(null=True)
    batch_size = models.BigIntegerField(null=True)
    train_rate = models.FloatField(null=True)
    eval_rate = models.FloatField(null=True)
    learning_rate = models.FloatField(null=True)
    max_epoch = models.IntegerField(null=True)
    gpu = models.BooleanField(null=True)
    gpu_id = models.IntegerField(null=True)

    class Meta:
        verbose_name = '任务'
        verbose_name_plural = verbose_name
        db_table = 'tb_task'

    def __str__(self):
        return self.task_name
