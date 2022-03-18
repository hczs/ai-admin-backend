import os
import platform
import threading
import time
from string import Template

from django.conf import settings
from loguru import logger

from business.enums import TaskStatusEnum, DatasetStatusEnum, TaskEnum
from business.evaluate import evaluate_insert
from business.models import Task, File
from business.show.task_show import generate_result_map
from common.utils import execute_cmd, parentheses_escape
from business.save_geojson import transfer_geo_json, get_geo_json


class ExecuteCommandThread(threading.Thread):
    """
    执行命令行命令线程，执行传入的命令str_command
    """

    def __init__(self, thread_name, str_command):
        self.str_command = str_command
        super(ExecuteCommandThread, self).__init__(name=thread_name)


    def set_log_file(self, task):
        # 从队列中取出放入数据库
        log_name = settings.LOG_QUEUE.get()
        logger.info('set_log_file-日志文件名称: {}', log_name)
        task.log_file_name = log_name
        task.save()

    def run(self):
        # 获取当前工作目录做备份
        backup_dir = os.getcwd()
        logger.info('start execute task, backup_dir: ' + backup_dir)
        # 切换到libcity程序目录跑命令
        os.chdir(settings.LIBCITY_PATH)
        logger.info('change dir: ' + os.getcwd())
        task = Task.objects.get(task_name=self.name)
        # 放入执行中队列中
        task_key = task.task_name + str(task.id)
        settings.IN_PROGRESS.append(task_key)
        # 任务开始执行，变更任务状态
        # 变更任务状态
        task.task_status = TaskStatusEnum.IN_PROGRESS.value
        task.save()
        # 执行
        self.str_command = settings.ACTIVE_VENV + ' && ' + self.str_command
        # Linux系统下需要对圆括号进行转义
        if platform.system().lower() == 'linux':
            self.str_command = parentheses_escape(self.str_command)
        logger.info('execute command: ' + self.str_command)
        ExpChildThread(self.name, self.str_command, backup_dir, task).start()
        # 执行后set log_file_name
        self.set_log_file(task)


class ExpChildThread(threading.Thread):
    """
    具体执行命令的线程
    """
    def __init__(self, thread_name, str_command, backup_dir, task):
        self.str_command = str_command
        self.backup_dir = backup_dir
        self.task = task
        super(ExpChildThread, self).__init__(name=thread_name)

    def rename_result(self, task):
        """
        重命名实验结果文件如npz、csv、json
        :param task: 实验对象
        """
        # evaluate_cache文件夹下文件按照创建时间排序
        file_dir = settings.EVALUATE_PATH_PREFIX + str(task.exp_id) + settings.EVALUATE_PATH_SUFFIX
        file_list = os.listdir(file_dir)
        file_list = sorted(file_list, key=lambda x: os.path.getctime(os.path.join(file_dir, x)),
                           reverse=True)
        logger.info('evaluate_cache文件夹下文件按照创建时间排序: {}', file_list)
        # 命名方式模板 task_id唯一，依靠task_id来定位具体文件
        result_template = Template("${task_id}_${model}_${dataset}_result.${suffix}")
        evaluate_template = Template("${task_id}_${model}_${dataset}.${suffix}")
        # 不同任务类型，结果文件不一样
        if task.task == TaskEnum.TRAFFIC_STATE_PRED.value or task.task == TaskEnum.ETA.value:
            # 交通状态和到达时间估计是一类 指标文件csv和结果文件npz
            for file in file_list:
                if os.path.splitext(file)[1] == '.csv':
                    new_name = evaluate_template.safe_substitute(task_id=task.id, model=task.model,
                                                                 dataset=task.dataset, suffix='csv')
                    os.rename(file_dir + file, file_dir + new_name)
                    break
            for file in file_list:
                if os.path.splitext(file)[1] == '.npz':
                    new_name = result_template.safe_substitute(task_id=task.id, model=task.model,
                                                               dataset=task.dataset, suffix='npz')
                    os.rename(file_dir + file, file_dir + new_name)
                    break
        elif task.task == TaskEnum.MAP_MATCHING.value:
            rename_csv = True
            rename_json = True
            # 路网匹配 指标文件csv和 结果文件geo json
            for file in file_list:
                if rename_csv and os.path.splitext(file)[1] == '.csv':
                    new_name = evaluate_template.safe_substitute(task_id=task.id, model=task.model,
                                                                 dataset=task.dataset, suffix='csv')
                    os.rename(file_dir + file, file_dir + new_name)
                    rename_csv = False
                if rename_json and os.path.splitext(file)[1] == '.json':
                    new_name = result_template.safe_substitute(task_id=task.id, model=task.model,
                                                               dataset=task.dataset, suffix='json')
                    os.rename(file_dir + file, file_dir + new_name)
                    rename_json = False
        elif task.task == TaskEnum.TRAJ_LOC_PRED.value:
            # 轨迹下一跳  指标文件json 无结果文件
            for file in file_list:
                if os.path.splitext(file)[1] == '.json':
                    new_name = evaluate_template.safe_substitute(task_id=task.id, model=task.model,
                                                                 dataset=task.dataset, suffix='json')
                    os.rename(file_dir + file, file_dir + new_name)
                    break
        elif task.task == TaskEnum.ROAD_REPRESENTATION.value:
            # 路网表征学习 结果文件csv 无指标文件
            for file in file_list:
                if os.path.splitext(file)[1] == '.csv':
                    new_name = result_template.safe_substitute(task_id=task.id, model=task.model,
                                                                 dataset=task.dataset, suffix='csv')
                    os.rename(file_dir + file, file_dir + new_name)
                    break

    def run(self) -> None:
        task = self.task
        task_key = task.task_name + str(task.id)
        status, output = execute_cmd(self.str_command)
        if status == 0:
            # 更新为已完成状态
            task.task_status = TaskStatusEnum.COMPLETED.value
            # 执行完毕后，修改相关文件名称
            self.rename_result(task)
            # 评价指标入库
            evaluate_insert(task)
            # 生成dataset和result对比的地图文件
            generate_result_map(task)
        if status == 1:
            # 更新任务状态，表示执行出错
            task.task_status = TaskStatusEnum.ERROR.value
        task.execute_end_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())  # 任务结束时间
        # 更新执行信息
        task.execute_msg = str(output, "utf-8")
        task.save()
        # 返回原工作目录
        os.chdir(self.backup_dir)
        logger.info('execute completed! change path to: ' + os.getcwd())
        settings.IN_PROGRESS.remove(task_key)
        settings.COMPLETED.append(task_key)


class ExecuteGeojsonThread(threading.Thread):
    """
    生成geojson文件
    参数：
    extract_path    压缩包提取路径
    thread_name     文件名称（不带提取路径）
    """

    def __init__(self, extract_path, thread_name):
        self.file_name = thread_name
        self.extract_path = extract_path
        super(ExecuteGeojsonThread, self).__init__(name=thread_name)

    def run(self):
        settings.IN_PROGRESS.append(self.file_name)
        file_view_status = DatasetStatusEnum.UN_PROCESS.value
        file_obj = File.objects.get(file_name=self.file_name)
        file_form_status = get_geo_json(self.file_name, self.extract_path + '_geo_json')
        if file_form_status == DatasetStatusEnum.PROCESSING_COMPLETE.value:
            logger.info(self.file_name + 'geojson文件生成完毕')
            # 处理完毕，更新数据集状态
            file_obj.dataset_status = file_view_status
        else:
            logger.error(self.file_name + '无法生成geojson文件')
            file_obj.dataset_status = file_form_status
        file_obj.save()
        settings.IN_PROGRESS.remove(self.file_name)
        settings.COMPLETED.append(self.file_name)


class ExecuteGeoViewThread(threading.Thread):
    """
    执行生成原子文件数据集可视化的线程
    参数：
    extract_path    压缩包提取路径
    thread_name     文件名称（不带提取路径）
    background_id   背景图id
    """

    def __init__(self, extract_path, thread_name, background_id):
        # self.str_command = str_command
        self.file_name = thread_name
        self.extract_path = extract_path
        self.background_id = background_id
        super(ExecuteGeoViewThread, self).__init__(name=thread_name)

    def run(self):
        settings.IN_PROGRESS.append(self.file_name)
        file_obj = File.objects.get(file_name=self.file_name)
        file_view_status = DatasetStatusEnum.PROCESSING.value
        try:
            if os.listdir(self.extract_path + '_geo_json') is not None:
                print(1234)
                file_view_status = transfer_geo_json(self.extract_path + '_geo_json', self.file_name,
                                                     self.background_id)
                print(file_view_status)
        except Exception as ex:
            file_view_status = DatasetStatusEnum.ERROR.value
            logger.error('ExecuteGeoViewThread transfer_geo_json 异常：{}', ex)
        # 处理完毕，更新数据集状态
        if file_view_status == DatasetStatusEnum.SUCCESS.value or file_view_status == DatasetStatusEnum.SUCCESS_stat.value:
            logger.info(self.file_name + "数据可视化处理完毕")
        else:
            logger.info(self.file_name + "数据可视化处理失败")
        file_obj.dataset_status = file_view_status
        file_obj.save()
        settings.IN_PROGRESS.remove(self.file_name)
        settings.COMPLETED.append(self.file_name)
