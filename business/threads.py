import os
import threading
import time

from business.models import Task


class ExecuteCommandThread(threading.Thread):
    """
    执行命令行命令线程，执行传入的命令str_command
    """
    def __init__(self, thread_name, str_command):
        self.str_command = str_command
        super(ExecuteCommandThread, self).__init__(name=thread_name)

    def run(self):
        task = Task.objects.get(task_name=self.name)
        # 任务开始执行，变更任务状态
        # 变更任务状态
        task.task_status = 1
        task.save()
        # 执行
        os.system(self.str_command)
        # 任务线程结束，更新任务状态
        task.task_status = 2  # 更新为已完成状态
        task.execute_end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())  # 任务结束时间
        task.save()
