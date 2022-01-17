import os
import shutil
import tempfile
import time
import zipfile

from django.conf import settings
from django.core import serializers
from django.http import FileResponse
from django.shortcuts import render

# Create your views here.
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from loguru import logger
from rest_framework import status, renderers, mixins
from rest_framework.decorators import action, renderer_classes
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, ListModelMixin
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from business.enums import TaskStatusEnum, DatasetStatusEnum
from business.filter import FileFilter, TaskFilter
from business.models import File, Task, TrafficStatePredAndEta, MapMatching, TrajLocPred
from business.models import File, Task
from business.save_geojson import get_geo_json
from business.scheduler import task_execute_at, task_is_exists, remove_task
from business.serializers import FileSerializer, TaskSerializer, TaskListSerializer, FileListSerializer, \
    TrafficStateEtaSerializer, MapMatchingSerializer, TrajLocPredSerializer
from business.evaluate import evaluate_insert
from business.serializers import FileSerializer, TaskSerializer, TaskListSerializer, FileListSerializer
from business.threads import ExecuteCommandThread, ExecuteGeojsonThread
from common.response import PassthroughRenderer
from common.utils import read_file_str, generate_download_file
from bs4 import BeautifulSoup


class FileViewSet(CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, ListModelMixin, GenericViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    parser_classes = [MultiPartParser, JSONParser]
    filter_class = FileFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return FileListSerializer
        else:
            return FileSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 有些zip当中存在其他类型文件（如.grid），需要核实
        atomic_file_ext = ['.geo', '.usr', '.rel', '.dyna', '.ext', '.json', '.grid']
        my_file = self.request.FILES.get('dataset', None)
        if not my_file:
            return Response(data={'detail': '未检测到文件！'}, status=status.HTTP_400_BAD_REQUEST)
        if 'zip' not in my_file.content_type:
            return Response(data={'detail': '请上传zip类型的文件！'}, status=status.HTTP_400_BAD_REQUEST)
        # 数据包文件格式检查
        zip_file = zipfile.ZipFile(my_file)
        zip_list = zip_file.namelist()
        for e in zip_list:
            file_name, ext = os.path.splitext(e)
            if (ext != "" or len(ext) != 0) and ext not in atomic_file_ext:
                return Response(data={'detail': '数据包中文件格式不正确，请上传原子文件'}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        """
        数据集文件上传处理
        """
        my_file = self.request.FILES.get('dataset', None)
        logger.info('已接受到文件，正在进行处理，文件名: ' + my_file.name)
        start = time.time()
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
        logger.info('文件上传完毕，文件名: ' + file_name)
        # 生成geojson的json文件
        url = settings.ADMIN_FRONT_HTML_PATH + 'homepage.html'  # 网页地址
        soup = BeautifulSoup(open(url, encoding='utf-8'), features='html.parser')
        content = str.encode(soup.prettify())  # 获取页面内容
        fp = open(settings.ADMIN_FRONT_HTML_PATH + file_name + ".html", "w+b")  # 打开一个文本文件
        fp.write(content)  # 写入数据
        fp.close()  # 关闭文件
        end = time.time()
        logger.info('上传文件初步处理运行时间: {} s；下面进行geojson和html文件的生成', end - start)
        # 启动执行任务线程，使用json生成folium的html展示页面
        ExecuteGeojsonThread(extract_path, file_name).start()

    def perform_destroy(self, instance):
        # 删除记录先删除对应文件
        if os.path.isfile(instance.file_path):
            os.remove(instance.file_path)
        if os.path.isdir(instance.extract_path):
            shutil.rmtree(instance.extract_path)
        if os.path.isdir(instance.extract_path + '_geo_json'):
            shutil.rmtree(instance.extract_path + '_geo_json')
        if os.path.isfile(settings.ADMIN_FRONT_HTML_PATH + instance.file_name + '.html'):
            os.remove(settings.ADMIN_FRONT_HTML_PATH + instance.file_name + '.html')
        instance.delete()

    @renderer_classes((PassthroughRenderer,))
    @action(methods=['get'], detail=False)
    def download(self, request):
        """
        数据集样例文件下载
        """
        return generate_download_file(settings.DATASET_EXAMPLE_PATH)

    @action(methods=['get'], detail=True)
    def get_gis_view(self, request, *args, **kwargs):
        """
        根据任务id获取geojson转化的gis图象地址
        """
        file = self.get_object()
        # print(file)
        # file_name = file.file_name # wheather pk or exp_id
        file_gis_path = str(file) + ".html"
        return file_gis_path


class TaskViewSet(ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    filter_class = TaskFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return TaskListSerializer
        else:
            return TaskSerializer

    @action(methods=['get'], detail=True)
    def get_log(self, *args, **kwargs):
        """
        获取指定任务的运行日志
        1.正在执行（1），尝试读取log文件内容，返回
        2.执行出错（-1） or 已完成（2），读取executeMsg返回
        """
        task = self.get_object()
        if task.task_status == TaskStatusEnum.IN_PROGRESS.value:
            file_list = os.listdir(settings.LOG_PATH)
            log_file = settings.LOG_PATH
            for file in file_list:
                if os.path.splitext(file)[0].split('-')[0] == str(task.id):
                    log_file += file
                    break
            if log_file != settings.LOG_PATH:
                log_content = read_file_str(log_file)
                return Response(log_content, status=status.HTTP_200_OK)
            else:
                return Response(data={'detail': '日志文件不存在！'}, status=status.HTTP_400_BAD_REQUEST)
        elif task.task_status == TaskStatusEnum.ERROR.value or task.task_status == TaskStatusEnum.COMPLETED.value:
            return Response(task.execute_msg, status=status.HTTP_200_OK)
        else:
            return Response(data={'detail': '任务未开始！'}, status=status.HTTP_400_BAD_REQUEST)

    @renderer_classes((PassthroughRenderer,))
    @action(methods=['get'], detail=True)
    def download_log(self, *args, **kwargs):
        """
        下载指定任务的日志文件
        """
        task = self.get_object()
        file_list = os.listdir(settings.LOG_PATH)
        log_file = settings.LOG_PATH
        for file in file_list:
            if os.path.splitext(file)[0].split('-')[0] == str(task.id):
                log_file += file
                break
        if log_file == settings.LOG_PATH:
            # 证明没有对应日志文件，直接生成文件返回
            file_obj = tempfile.NamedTemporaryFile()
            file_obj.name = 'error.log'
            file_obj.write(task.execute_msg.encode('utf-8'))
            file_obj.seek(0)
            response_file = FileResponse(file_obj)
            response_file['content_type'] = "application/octet-stream"
            response_file['Content-Disposition'] = 'attachment; filename=' + file_obj.name
            return response_file
        else:
            return generate_download_file(log_file)

    @action(methods=['get'], detail=True)
    def execute(self, request, *args, **kwargs):
        """
        执行任务，需要传递execute_time参数为具体执行时间，如果不传参代表立即执行
        """
        execute_time = request.query_params.get('execute_time')
        task = self.get_object()
        # 检查任务是否可执行
        if task.task_status != TaskStatusEnum.NOT_STARTED.value and task.task_status != TaskStatusEnum.ERROR.value:
            return Response(data={'detail': '任务正在执行中或已完成，请勿重复执行！'}, status=status.HTTP_400_BAD_REQUEST)
        # 获取任务数据，组装命令
        task_param = ['task', 'model', 'dataset', 'config_file', 'saved_model', 'train', 'batch_size', 'train_rate',
                      'eval_rate', 'learning_rate', 'max_epoch', 'gpu', 'gpu_id']
        str_command = 'python ' + settings.RUN_MODEL_PATH + ' --exp_id ' + str(task.pk)
        for param in task_param:
            param_value = getattr(task, param)
            if param_value is not None:
                if param == 'config_file':
                    path, param_value = os.path.split(param_value)
                str_command += ' --' + param + ' ' + str(param_value)
        # 检查任务是否已经加入过队列中，如果已经存在，把之前的移除，以本次提交为准
        if task_is_exists(str(task.id)):
            remove_task(str(task.id))
        # 添加任务到执行队列中，不传execute_time就代表立即执行
        task_execute_at(task.task_name, str_command, execute_time, str(task.id))
        # 更新任务执行时间信息
        if execute_time:
            task.execute_time = execute_time
        else:
            task.execute_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        # 如果是执行出错重新执行，需要把结束时间置空
        if task.task_status == TaskStatusEnum.ERROR.value:
            task.execute_end_time = None
        task.save()
        return Response(status=status.HTTP_200_OK)

    @swagger_auto_schema(methods=['post'], request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['task_name'],
        properties={'task_name': openapi.Schema(type=openapi.TYPE_STRING)}
    ))
    @action(methods=['post'], detail=False)
    def exists(self, request):
        """
        检测任务是否存在
        """
        task_name = request.data.get('task_name')
        tasks = Task.objects.filter(task_name=task_name).all()
        if len(tasks) == 0:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(data={'msg': '任务已存在！', 'id': tasks[0].id}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], detail=False)
    def upload(self, request):
        """
        任务配置文件上传，返回文件存储路径
        此配置文件应该放在AI项目根目录下，因为多任务，所以要根据配置文件名来区分
        """
        my_file = request.FILES.get('config', None)
        if not my_file:
            return Response(data={'detail': '未检测到文件！'}, status=status.HTTP_400_BAD_REQUEST)
        path = settings.TASK_PARAM_PATH
        # 目录不存在则新建目录
        if not os.path.isdir(path):
            os.makedirs(path)
        original_file_name, ext = os.path.splitext(my_file.name)
        file_path = file_duplication_handle(original_file_name, ext, path, 1)
        path, file_name_and_ext = os.path.split(file_path)
        with open(os.path.join(path, file_name_and_ext), 'wb+') as f:
            for chunk in my_file.chunks():
                f.write(chunk)
        # 返回文件存储路径
        return Response(file_path)

    def perform_create(self, serializer):
        """
        创建任务时添加任务创建者
        """
        account = self.request.user
        serializer.save(creator=account)

    @renderer_classes((PassthroughRenderer,))
    @action(methods=['get'], detail=False)
    def download_config(self, request):
        """
        参数配置文件样例文件下载
        """
        return generate_download_file(settings.TASK_PARAM_EXAMPLE_PATH)

    @action(methods=['get'], detail=True)
    def get_result(self, request, *args, **kwargs):
        """
        根据任务id获取结果
        """
        task = self.get_object()
        print(task)
        # 变更任务状态
        if task.task_status != 2:
            return Response(data={'detail': '任务尚未输出结果'}, status=status.HTTP_400_BAD_REQUEST)
        file_id = task.pk  # wheather pk or exp_id
        file_path = settings.RESULT_PATH + str(file_id)
        return Response(file_path)


class TrafficStateEtaViewSet(ModelViewSet):
    """
    交通状态预测任务和到达时间估计任务评价指标查询
    """
    queryset = TrafficStatePredAndEta.objects.all()
    serializer_class = TrafficStateEtaSerializer
    filterset_fields = ['task']

    @renderer_classes((PassthroughRenderer,))
    @action(methods=['get'], detail=False)
    def download(self, request, *args, **kwargs):
        """
        指定任务指定指标文件下载
        """
        task_id = request.query_params.get('task')
        # 根据id找到对应指标文件
        # 数据准备
        file_dir = settings.EVALUATE_PATH_PREFIX + str(task_id) + settings.EVALUATE_PATH_SUFFIX
        if os.path.isdir(file_dir):
            # 扫描文件夹下所有文件
            file_list = os.listdir(file_dir)
            for file in file_list:
                if os.path.splitext(file)[1] == '.csv' or os.path.splitext(file)[1] == '.json':
                    file_path = file_dir + file
                    return generate_download_file(file_path)
        return Response(data={'detail': '指标文件不存在！'}, status=status.HTTP_400_BAD_REQUEST)


class MapMatchingViewSet(ModelViewSet):
    """
    路网匹配评价指标
    """
    queryset = MapMatching.objects.all()
    serializer_class = MapMatchingSerializer
    filterset_fields = ['task']


class TrajLocPredViewSet(ModelViewSet):
    """
    轨迹下一跳评价指标
    """
    queryset = TrajLocPred.objects.all()
    serializer_class = TrajLocPredSerializer
    filterset_fields = ['task']


def file_duplication_handle(original_file_name, ext, path, index):
    """
    检测文件名是否重复，若重复则将文件名加(index)后缀
    """
    file_path = path + original_file_name + ext
    if os.path.isfile(file_path):
        tmp_file_name = original_file_name + '(' + str(index) + ')'
        file_path = path + tmp_file_name + ext
        if os.path.isfile(file_path):
            return file_duplication_handle(original_file_name, ext, path, index + 1)
        else:
            return file_path
    else:
        return file_path


def extract_without_folder(arc_name, full_item_name, folder):
    """
    解压压缩包中的指定文件到指定目录

    :param arc_name: 压缩包文件
    :param full_item_name: 压缩包中指定文件的全路径，相对压缩包的相对路径
    :param folder: 解压的目标目录，绝对路径
    """
    with zipfile.ZipFile(arc_name) as zf:
        file_data = zf.read(full_item_name)
    # 中文乱码解决
    full_item_name = full_item_name.encode('cp437').decode('gbk')
    with open(os.path.join(folder, os.path.basename(full_item_name)), "wb") as file_out:
        file_out.write(file_data)
