from rest_framework import serializers

import common.utils
from business.models import File, Task


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = '__all__'


class FileListSerializer(serializers.ModelSerializer):

    class Meta:
        model = File
        fields = '__all__'

    def to_representation(self, instance):
        data = super(FileListSerializer, self).to_representation(instance)
        # 取出要进行处理的字段
        data['file_size'] = common.utils.pybyte(data['file_size'])
        return data


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'


class TaskListSerializer(serializers.ModelSerializer):
    creator = serializers.StringRelatedField()

    class Meta:
        model = Task
        fields = '__all__'
