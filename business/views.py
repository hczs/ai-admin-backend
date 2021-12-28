import os
import shutil
import time
import zipfile

from django.conf import settings
from django.http import FileResponse
from django.shortcuts import render

# Create your views here.
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, renderers
from rest_framework.decorators import action, renderer_classes
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin, RetrieveModelMixin, ListModelMixin
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from business.filter import FileFilter, TaskFilter
from business.models import File, Task
from business.scheduler import task_execute_at, task_is_exists, remove_task
from business.serializers import FileSerializer, TaskSerializer, TaskListSerializer, FileListSerializer
from common.response import PassthroughRenderer


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
        atomic_file_ext = ['.geo', '.usr', '.rel', '.dyna', '.ext', '.json']
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
        serializer.save(file_name=file_name, file_path=file_path, file_size=file_size, extract_path=extract_path)

    def perform_destroy(self, instance):
        instance.delete()
        # 删除记录后删除对应文件
        os.remove(instance.file_path)
        shutil.rmtree(instance.extract_path)

    @renderer_classes((PassthroughRenderer,))
    @action(methods=['get'], detail=False)
    def download(self, request):
        """
        数据集样例文件下载
        """
        file_path = settings.DATASET_EXAMPLE_PATH
        response_file = FileResponse(open(file_path, 'rb'))
        response_file['content_type'] = "application/octet-stream"
        response_file['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
        return response_file


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
    def execute(self, request, *args, **kwargs):
        """
        执行任务，需要传递execute_time参数为具体执行时间，如果不传参代表立即执行
        """
        execute_time = request.query_params.get('execute_time')
        task = self.get_object()
        # 检查任务是否可执行
        if task.task_status != 0:
            return Response(data={'detail': '任务正在执行中或已完成，请勿重复执行！'}, status=status.HTTP_400_BAD_REQUEST)
        # 获取任务数据，组装命令
        task_param = ['task', 'model', 'dataset', 'config_file', 'saved_model', 'train', 'batch_size', 'train_rate',
                      'eval_rate', 'learning_rate', 'max_epoch', 'gpu', 'gpu_id']
        str_command = 'python ' + settings.RUN_MODEL_PATH
        for param in task_param:
            param_value = getattr(task, param)
            if param == 'config_file' and param_value is not None:
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
