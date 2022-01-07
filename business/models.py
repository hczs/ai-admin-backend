from django.utils import timezone

from django.db import models

# Create your models here.
from authentication.models import Account
from common.models import BaseModel


class File(BaseModel):
    file_name = models.CharField(max_length=50, null=True)
    file_size = models.BigIntegerField(null=True)
    file_path = models.CharField(max_length=200, null=True)
    extract_path = models.CharField(max_length=200, null=True)

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
    execute_time = models.DateTimeField(null=True)
    execute_end_time = models.DateTimeField(null=True)
    task_status = models.IntegerField(default=0)
    execute_msg = models.TextField(null=True)
    # 以下是任务执行参数
    task = models.CharField(max_length=30)
    model = models.CharField(max_length=30)
    dataset = models.CharField(max_length=100)
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


class TrafficStatePredAndEta(models.Model):
    MAE = models.CharField(max_length=30)
    MAPE = models.CharField(max_length=30)
    MSE = models.CharField(max_length=30)
    RMSE = models.CharField(max_length=30)
    masked_MAE = models.CharField(max_length=30)
    masked_MAPE = models.CharField(max_length=30)
    masked_MSE = models.CharField(max_length=30)
    masked_RMSE = models.CharField(max_length=30)
    R2 = models.CharField(max_length=30)
    EVAR = models.CharField(max_length=30)
    Precision = models.CharField(max_length=30)
    Recall = models.CharField(max_length=30)
    F1_Score = models.CharField(max_length=30)
    MAP = models.CharField(max_length=30)
    PCC = models.CharField(max_length=30)
    task = models.ForeignKey(Task, db_constraint=False, on_delete=models.CASCADE)

    class Meta:
        verbose_name = '交通状态预测任务和到达时间预测评价指标'
        verbose_name_plural = verbose_name
        db_table = 'traffic_state_eta_pred'


class MapMatching(models.Model):
    RMF = models.CharField(max_length=30)
    AN = models.CharField(max_length=30)
    AL = models.CharField(max_length=30)
    task = models.ForeignKey(Task, db_constraint=False, on_delete=models.CASCADE)

    class Meta:
        verbose_name = '路网匹配评价指标'
        verbose_name_plural = verbose_name
        db_table = 'map_matching'


class TrajLocPred(models.Model):
    Recall = models.CharField(max_length=30)
    task = models.ForeignKey(Task, db_constraint=False, on_delete=models.CASCADE)

    class Meta:
        verbose_name = '轨迹下一跳预测评价指标'
        verbose_name_plural = verbose_name
        db_table = 'traj_loc_pred'
