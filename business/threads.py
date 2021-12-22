import os
import threading
import time

from django.conf import settings

from business.models import Task


class ExecuteCommandThread(threading.Thread):
    """
    执行命令行命令线程，执行传入的命令str_command
    """
    def __init__(self, thread_name, str_command):
        self.str_command = str_command
        super(ExecuteCommandThread, self).__init__(name=thread_name)

    def run(self):
        os.system(self.str_command)
        # 任务线程结束，更新任务状态
        task = Task.objects.get(task_name=self.name)
        task.task_status = 2  # 更新为已完成状态
        task.save()
        # 把自己加到监控线程中
        # MonitorThread(self.name, self.name + '-MonitorThread').start()


# class MonitorThread(threading.Thread):
#     """
#     监控线程，监控某个线程实例是否运行结束
#     """
#     def __init__(self, monitored_thread_name, thread_name):
#         self.monitored_thread_name = monitored_thread_name
#         super(MonitorThread, self).__init__(name=thread_name)
#
#     def run(self):
#         is_break = False
#         threads = threading.enumerate()  # 所有线程实例
#         print("正在监控thread: " + self.monitored_thread_name)
#         while True:
#             time.sleep(settings.MONITORING_FREQUENCY)
#             for instance in threads:
#                 if instance.getName() == self.monitored_thread_name:
#                     if not instance.is_alive():
#                         print(instance.getName() + '结束了')
#                         is_break = True
#             if is_break:
#                 break
#         # 任务线程结束，更新任务状态
#         task = Task.objects.get(task_name=self.monitored_thread_name)
#         task.task_status = 2  # 更新为已完成状态
#         task.save()
