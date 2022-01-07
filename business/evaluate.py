import csv
import json
import os

from django.conf import settings

from business.enums import TaskEnum
from business.models import TrafficStatePredAndEta, MapMatching, TrajLocPred


def evaluate_insert(task):
    """
    指标数据入库

    :param task: 评价指标所属任务对象
    """
    # 数据准备
    file_dir = settings.EVALUATE_PATH_PREFIX + str(task.id) + settings.EVALUATE_PATH_SUFFIX
    # 扫描文件夹下所有文件
    file_list = os.listdir(file_dir)
    for file in file_list:
        if os.path.splitext(file)[1] == '.csv':
            csv_insert(file_dir + file, task)
        if os.path.splitext(file)[1] == '.json':
            json_insert(file_dir + file, task)


def csv_insert(csv_path, task):
    """
    读取csv评价指标文件，插入到相应表中

    :param csv_path: csv文件路径
    :param task: 评价指标所属任务对象
    """
    csv_reader = csv.reader(open(csv_path))
    csv_reader.__next__()  # 跳过首行
    values = []
    if task.task == TaskEnum.TRAFFIC_STATE_PRED.value or task.task == TaskEnum.ETA.value:
        for line in csv_reader:
            if len(line) == 10:
                values.append(TrafficStatePredAndEta(MAE=line[0], MAPE=line[1], MSE=line[2], RMSE=line[3],
                                                     masked_MAE=line[4], masked_MAPE=line[5], masked_MSE=line[6],
                                                     masked_RMSE=line[7], R2=line[8], EVAR=line[9], task=task))
            if len(line) == 15:
                values.append(TrafficStatePredAndEta(MAE=line[0], MAPE=line[1], MSE=line[2], RMSE=line[3],
                                                     masked_MAE=line[4], masked_MAPE=line[5], masked_MSE=line[6],
                                                     masked_RMSE=line[7], R2=line[8], EVAR=line[9], Precision=line[10],
                                                     Recall=line[11], F1_Score=line[12], MAP=line[13], PCC=line[14],
                                                     task=task))
        TrafficStatePredAndEta.objects.bulk_create(values)
    if task.task == TaskEnum.MAP_MATCHING.value:
        for line in csv_reader:
            values.append(MapMatching(RMF=line[0], AN=line[1], AL=line[2], task=task))
        MapMatching.objects.bulk_create(values)


def json_insert(json_path, task):
    # 轨迹下一跳预测任务指标为json文件，就一列recall
    if task.task == TaskEnum.TRAJ_LOC_PRED.value:
        with open(json_path, 'r', encoding='UTF-8') as f:
            json_dict = json.load(f)
        for key in json_dict:
            TrajLocPred(Recall=json_dict[key], task=task).save()
