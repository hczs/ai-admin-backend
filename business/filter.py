import django_filters
from django_filters.rest_framework import FilterSet

from business.models import File, Task


class FileFilter(FilterSet):
    """
    文件查询条件过滤
    """
    # 创建时间区间查询
    begin = django_filters.DateTimeFilter(field_name='create_time', lookup_expr='gte')
    end = django_filters.DateTimeFilter(field_name='create_time', lookup_expr='lte')
    # 文件名模糊查询
    file_name = django_filters.CharFilter(field_name='file_name', lookup_expr='icontains')

    class Meta:
        model = File
        fields = ['begin', 'end', 'file_name']


class TaskFilter(FilterSet):
    """
    文件查询条件过滤
    """
    # 创建时间区间查询
    begin = django_filters.DateTimeFilter(field_name='create_time', lookup_expr='gte')
    end = django_filters.DateTimeFilter(field_name='create_time', lookup_expr='lte')
    # 文件名模糊查询
    task_name = django_filters.CharFilter(field_name='task_name', lookup_expr='icontains')

    class Meta:
        model = Task
        fields = ['begin', 'end', 'task_name']
