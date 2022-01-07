import os
import threading
import time

from django.conf import settings

from business.enums import TaskStatusEnum
from business.evaluate import evaluate_insert
from business.models import Task
from common.utils import execute_cmd


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
        print('backup_dir: ', backup_dir)
        # 切换到libcity程序目录跑命令
        os.chdir(settings.LIBCITY_PATH)
        print('切换后：', os.getcwd())
        task = Task.objects.get(task_name=self.name)
        # 任务开始执行，变更任务状态
        # 变更任务状态
        task.task_status = TaskStatusEnum.IN_PROGRESS.value
        task.save()
        print(self.str_command)
        # 执行
        self.str_command = settings.ACTIVE_VENV + ' && ' + self.str_command
        status, output = execute_cmd(self.str_command)
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
        print('执行结束，切回原来的：', os.getcwd())
