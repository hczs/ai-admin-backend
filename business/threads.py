import os
import threading
import time
import zipfile

from bs4 import BeautifulSoup
from django.conf import settings
from loguru import logger

from business.enums import TaskStatusEnum, DatasetStatusEnum
from business.evaluate import evaluate_insert
from business.models import Task, File
from common.utils import execute_cmd, parentheses_escape, extract_without_folder, file_duplication_handle
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


class HandleUploadFileThread(threading.Thread):
    """
    处理上传的文件
    """

    def __init__(self, my_file, serializer):
        # self.str_command = str_command
        self.my_file = my_file
        self.serializer = serializer
        super(HandleUploadFileThread, self).__init__()

    def run(self):
        my_file = self.my_file
        serializer = self.serializer
        path = settings.DATASET_PATH
        # 目录不存在则新建目录
        if not os.path.isdir(path):
            os.makedirs(path)
        file_size = my_file.size
        original_file_name, ext = os.path.splitext(my_file.name)
        file_path = file_duplication_handle(original_file_name, ext, path, 1)  # zip文件路径
        path, file_name_and_ext = os.path.split(file_path)
        file_name, ext = os.path.splitext(file_name_and_ext)
        extract_path = os.path.join(path, file_name)  # 解压目录，解压到zip文件名下的文件夹目录
        # 创建解压目录
        if not os.path.isdir(extract_path):
            os.makedirs(extract_path)
        with open(os.path.join(path, file_name_and_ext), 'wb+') as f:
            for chunk in my_file.chunks():
                f.write(chunk)
            # 写入完毕解压缩文件
            zip_file = zipfile.ZipFile(f)
            zip_list = zip_file.namelist()
            for every in zip_list:
                tmp_name, ext = os.path.splitext(every)
                if (ext != "" or len(ext) != 0) and tmp_name:
                    extract_without_folder(f, every, extract_path)
            zip_file.close()
        serializer.save(file_name=file_name, file_path=file_path, file_size=file_size,
                        extract_path=extract_path, dataset_status=DatasetStatusEnum.PROCESSING.value)
        # 生成geojson的json文件
        url = settings.ADMIN_FRONT_HTML_PATH + 'homepage.html'  # 网页地址
        soup = BeautifulSoup(open(url, encoding='utf-8'), features='html.parser')
        content = str.encode(soup.prettify())  # 获取页面内容
        fp = open(settings.ADMIN_FRONT_HTML_PATH + file_name + ".html", "w+b")  # 打开一个文本文件
        fp.write(content)  # 写入数据
        fp.close()  # 关闭文件
        # 启动执行任务线程，使用json生成folium的html展示页面
        ExecuteGeojsonThread(extract_path, file_name).start()


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
        # 处理完毕，更新数据集状态
        file_obj.dataset_status = file_view_status
        file_obj.save()
