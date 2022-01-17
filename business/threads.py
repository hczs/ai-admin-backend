import os
import threading
import time

from django.conf import settings
from loguru import logger

from business.enums import TaskStatusEnum, DatasetStatusEnum
from business.evaluate import evaluate_insert
from business.models import Task, File
from common.utils import execute_cmd, parentheses_escape
from business.save_geojson import transfer_geo_json, get_geo_json


class ExecuteCommandThread(threading.Thread):
    """
    执行命令行命令线程，执行传入的命令str_command
    """

    def __init__(self, thread_name, str_command):
        self.str_command = str_command
        super(ExecuteCommandThread, self).__init__(name=thread_name)

    def run(self):
        # 获取当前工作目录做备份
        backup_dir = os.getcwd()
        logger.info('start execute task, backup_dir: ' + backup_dir)
        # 切换到libcity程序目录跑命令
        os.chdir(settings.LIBCITY_PATH)
        logger.info('change dir: ' + os.getcwd())
        task = Task.objects.get(task_name=self.name)
        # 任务开始执行，变更任务状态
        # 变更任务状态
        task.task_status = TaskStatusEnum.IN_PROGRESS.value
        task.save()
        # 执行
        self.str_command = settings.ACTIVE_VENV + ' && ' + self.str_command
        logger.info('execute command: ' + parentheses_escape(self.str_command))
        status, output = execute_cmd(parentheses_escape(self.str_command))
        if status == 0:
            # 更新为已完成状态
            task.task_status = TaskStatusEnum.COMPLETED.value
            # 评价指标入库
            evaluate_insert(task)
        if status == 1:
            # 更新任务状态，表示执行出错
            task.task_status = TaskStatusEnum.ERROR.value
        task.execute_end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())  # 任务结束时间
        # 更新执行信息
        task.execute_msg = str(output, "utf-8")
        task.save()
        # 返回原工作目录
        os.chdir(backup_dir)
        logger.info('execute completed! change path to: ' + os.getcwd())


class ExecuteGeojsonThread(threading.Thread):
    """
    执行命令行命令线程，执行传入的命令str_command
    """

    def __init__(self, extract_path, thread_name):
        # self.str_command = str_command
        self.file_name = thread_name
        self.extract_path = extract_path
        super(ExecuteGeojsonThread, self).__init__(name=thread_name)

    def run(self):
        file_view_status = DatasetStatusEnum.ERROR.value
        file_obj = File.objects.get(file_name=self.file_name)
        file_form_status = get_geo_json(self.file_name, self.extract_path + '_geo_json')
        if file_form_status == DatasetStatusEnum.PROCESSING_COMPLETE.value:
            logger.info(self.file_name + 'geojson文件生成完毕')
            file_view_status = transfer_geo_json(self.extract_path + '_geo_json', self.file_name)
            logger.info(self.file_name + "数据可视化处理完毕")
        else:
            logger.info(self.file_name + '无法生成geojson文件')
        # 处理完毕，更新数据集状态
        file_obj.dataset_status = file_view_status
        file_obj.save()
